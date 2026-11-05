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
  await pagina.goto(BASE + ruta, { waitUntil: "networkidle" });
  if (esperar) await pagina.getByText(esperar).first().waitFor({ timeout: 150000 });
  await pagina.waitForTimeout(1800); // animaciones de entrada
  if (preparar) await preparar(pagina);
  await pagina.screenshot({ path: path.join(CARPETA, `${nombre}.png`), fullPage: completa });
  await pagina.close();
  console.log(`captura ${nombre}`);
}

(async () => {
  const navegador = await chromium.launch();
  try {
    await captura(navegador, "01-portada", "/", { esperar: "Eventos destacados", completa: true });
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
    await captura(navegador, "07-recuperar", "/recuperar", {
      esperar: "¿Olvidaste tu contraseña?",
      preparar: async (p) => {
        await p.fill("#correo", "ana.perez@ejemplo.com");
        await marcar(p, ["#correo", "button[type=submit]"]);
      },
    });
    await captura(navegador, "04-eventos", "/eventos", { esperar: "Ver plano de stands", completa: true });
    // El plano del primer evento publicado, con un stand seleccionado
    const pagina = await navegador.newPage({ viewport: VISTA });
    await pagina.goto(`${BASE}/eventos`, { waitUntil: "networkidle" });
    await pagina.getByText("Ver plano de stands").first().waitFor({ timeout: 150000 });
    const plano = await pagina.getByText("Ver plano de stands").first().getAttribute("href");
    await pagina.close();
    await captura(navegador, "05-plano-stands", plano, {
      esperar: "Cuadrícula de stands",
      completa: true,
      preparar: async (p) => {
        const stand = p.locator("button", { hasText: "m²" }).first();
        await stand.click();
        await p.waitForTimeout(500);
      },
    });
    await captura(navegador, "06-portada-oscuro", "/", { esperar: "Eventos destacados", tema: "dark" });
  } finally {
    await navegador.close();
  }
})();
