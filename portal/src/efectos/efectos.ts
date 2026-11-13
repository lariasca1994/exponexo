// Efectos globales (web y PWA): onda desde el punto del toque en los botones y en el menú, y
// temblor del botón de envío cuando aparece un aviso de error (role="alert"). Sin dependencias;
// si algo falla, la app sigue igual.
const reducir = () => window.matchMedia("(prefers-reduced-motion: reduce)").matches;
const BOTON = ".btn, .menu-op, .boton-topbar";

function onda(e: PointerEvent) {
  const b = (e.target as Element | null)?.closest?.<HTMLElement>(BOTON);
  if (!b || (b as HTMLButtonElement).disabled || reducir()) return;
  const r = b.getBoundingClientRect();
  const o = document.createElement("span");
  o.className = b.classList.contains("btn-primary") || b.classList.contains("boton-topbar-lleno") ? "onda" : "onda onda-suave";
  o.style.setProperty("--x", `${e.clientX - r.left}px`);
  o.style.setProperty("--y", `${e.clientY - r.top}px`);
  o.style.setProperty("--d", `${Math.max(r.width, r.height) * 2.2}px`);
  b.appendChild(o);
  o.addEventListener("animationend", () => o.remove());
}

function temblar(el: Element | null | undefined) {
  if (!el || reducir()) return;
  el.classList.remove("temblor");
  void (el as HTMLElement).offsetWidth;
  el.classList.add("temblor");
  el.addEventListener("animationend", () => el.classList.remove("temblor"), { once: true });
}

function vigilarErrores() {
  new MutationObserver((cambios) => {
    for (const cambio of cambios) {
      cambio.addedNodes.forEach((nodo) => {
        if (!(nodo instanceof HTMLElement)) return;
        const aviso = nodo.matches('[role="alert"]') ? nodo : nodo.querySelector('[role="alert"]');
        if (!aviso) return;
        const zona = aviso.closest("section, main") ?? document;
        temblar(zona.querySelector('form button[type="submit"]'));
      });
    }
  }).observe(document.body, { childList: true, subtree: true });
}

export function iniciarEfectos() {
  try {
    document.addEventListener("pointerdown", onda, { passive: true });
    vigilarErrores();
  } catch {
    // Los efectos son decorativos.
  }
}
