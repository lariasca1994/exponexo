// Genera automáticamente las capturas del manual de usuario contra el portal en producción.
// Cada formulario lleva marcadores numerados en rojo junto a sus campos (la numeración coincide
// con las tablas de docs/MANUAL.md) y los datos escritos son ficticios.
//
// Lo corre el workflow "Capturas del manual" (cada vez que cambia el portal y a mano); también:
//   npm install --no-save playwright && node docs/img/manual/generar.cjs
const path = require("node:path");
const { chromium } = require("playwright");

const BASE = process.env.URL_PORTAL || "https://exponexo-portal.vercel.app";
const CARPETA = __dirname;
const VISTA = { width: 1280, height: 800 };

async function marcar(pagina, selectores) {
  await pagina.evaluate((lista) => {
    document.querySelectorAll(".marcador-manual").forEach((m) => m.remove());
    lista.forEach((selector, i) => {
      const elemento = document.querySelector(selector);
      if (!elemento) return;
      const caja = elemento.getBoundingClientRect();
      const marca = document.createElement("div");
      marca.className = "marcador-manual";
      marca.textContent = String(i + 1);
      Object.assign(marca.style, {
        position: "absolute", zIndex: 9999, width: "24px", height: "24px", borderRadius: "50%",
        background: "#e11d48", color: "#fff", font: "700 13px Segoe UI, Arial, sans-serif",
        display: "grid", placeItems: "center", boxShadow: "0 0 0 3px #fff, 0 2px 6px rgba(0,0,0,.3)",
        left: `${caja.left + window.scrollX - 34}px`, top: `${caja.top + window.scrollY + caja.height / 2 - 12}px`,
      });
      document.body.appendChild(marca);
    });
  }, selectores);
}

async function captura(navegador, nombre, ruta, { esperar, preparar, completa = false, tema = "light" } = {}) {
  const pagina = await navegador.newPage({ viewport: VISTA, colorScheme: tema });
  // Los servicios escalan a cero: la primera carga puede esperar a que despierten
  await pagina.goto(BASE + ruta, { waitUntil: "load", timeout: 150000 });
  if (esperar) await pagina.getByText(esperar).first().waitFor({ timeout: 150000 });
  await pagina.waitForLoadState("networkidle", { timeout: 20000 }).catch(() => {});
  await pagina.waitForTimeout(1800); // animaciones de entrada
  if (preparar) await preparar(pagina);
  await pagina.screenshot({ path: path.join(CARPETA, `${nombre}.png`), fullPage: completa });
  await pagina.close();
  console.log(`captura ${nombre}`);
}

// Revisa que ninguna página pública se desborde a lo ancho en celular y tablet, y captura la portada en ambos.
async function pantallas(navegador) {
  for (const [ancho, alto, nombre] of [[800, 1280, "07-navegacion-tablet"], [390, 844, "08-navegacion-movil"]]) {
    const contexto = await navegador.newContext({ viewport: { width: ancho, height: alto }, isMobile: ancho < 500, hasTouch: true, locale: "es-CO" });
    const p = await contexto.newPage();
    for (const ruta of ["/", "/eventos", "/registro", "/ingreso", "/recuperar"]) {
      await p.goto(BASE + ruta, { waitUntil: "load", timeout: 150000 });
      await p.waitForLoadState("networkidle", { timeout: 20000 }).catch(() => {});
      await p.waitForTimeout(1200);
      const sobra = await p.evaluate(() => document.documentElement.scrollWidth - document.documentElement.clientWidth);
      if (sobra > 0) throw new Error(`${ancho}px ${ruta}: la página se desborda ${sobra} px`);
    }
    await p.goto(`${BASE}/eventos`, { waitUntil: "load", timeout: 150000 });
    await p.getByText("Ver plano de stands").first().waitFor({ timeout: 150000 });
    await p.waitForTimeout(1500);
    await p.screenshot({ path: path.join(CARPETA, `${nombre}.png`) });
    await contexto.close();
    console.log(`captura ${nombre}`);
  }
}

(async () => {
  const navegador = await chromium.launch({ args: ["--lang=es-CO"], env: { ...process.env, LANG: "es_CO.UTF-8", LANGUAGE: "es_CO:es" } });
  try {
    await captura(navegador, "01-portada", "/", { esperar: "Eventos destacados" });
    await captura(navegador, "02-registro", "/registro", {
      esperar: "Crear cuenta",
      preparar: async (p) => {
        await p.fill("#nombre", "Ana Pérez");
        await p.fill("#correo", "ana.perez@ejemplo.com");
        await p.selectOption("#rol", "expositor");
        await p.fill("#contrasena", "Ejemplo-Clave-2026");
        await marcar(p, ["#nombre", "#correo", "#rol", "#contrasena", "button[type=submit]"]);
      },
    });
    await captura(navegador, "03-ingreso", "/ingreso", {
      esperar: "Qué bueno",
      preparar: async (p) => {
        await p.fill("#correo", "ana.perez@ejemplo.com");
        await p.fill("#contrasena", "Ejemplo-Clave-2026");
        await marcar(p, ["#correo", "#contrasena", ".login-olvido", "button[type=submit]"]);
      },
    });
    await captura(navegador, "05-recuperar", "/recuperar", {
      esperar: "¿Olvidaste tu contraseña?",
      preparar: async (p) => {
        await p.fill("#correo", "ana.perez@ejemplo.com");
        await marcar(p, ["#correo", "button[type=submit]"]);
      },
    });
    await captura(navegador, "06-pantalla-principal", "/eventos", { esperar: "Ver plano de stands", completa: true });
    await pantallas(navegador);
    // El plano del primer evento publicado, con un stand seleccionado.
    const pagina = await navegador.newPage({ viewport: VISTA });
    await pagina.goto(`${BASE}/eventos`, { waitUntil: "load", timeout: 150000 });
    await pagina.getByText("Ver plano de stands").first().waitFor({ timeout: 150000 });
    const plano = await pagina.getByText("Ver plano de stands").first().getAttribute("href");
    await pagina.close();
    await captura(navegador, "09-consultar-plano", plano, {
      esperar: "Cuadrícula de stands",
      completa: true,
      preparar: async (p) => {
        const stand = p.locator("button", { hasText: "m²" }).first();
        await stand.click();
        await p.waitForTimeout(500);
      },
    });
    await captura(navegador, "16-no-encontrada", "/esta-pagina-no-existe", {});
    await captura(navegador, "17-sin-conexion", "/offline.html", {});
    await captura(navegador, "18-tema-oscuro", "/", { esperar: "Eventos destacados", tema: "dark" });
  } finally {
    await navegador.close();
  }
})().catch((e) => { console.error("ERROR:", e.message); process.exit(1); });
