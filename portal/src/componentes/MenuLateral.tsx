import { useCallback, useEffect, useLayoutEffect, useRef, useState, type CSSProperties, type ReactNode } from "react";
import { NavLink, useLocation, useNavigate } from "react-router-dom";

// Menú lateral con sesión: extendido o compacto (se recuerda en este equipo), indicador con haz
// de luz, fondo que sigue al ratón y etiqueta con el nombre en modo compacto. En el teléfono es
// una barra de vidrio flotante con cinco casillas; lo que no cabe va en la hoja "Más".
// Mismos enlaces y textos que tenía el encabezado, según el rol.

export interface OpcionMenu {
  to: string;
  texto: string;
  corto?: string;
  icono: ReactNode;
}

const CASILLAS_TELEFONO = 5;
const reducir = () => window.matchMedia("(prefers-reduced-motion: reduce)").matches;

function Icono({ d }: { d: string }) {
  return (
    <svg viewBox="0 0 24 24" width="20" height="20" aria-hidden="true" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
      <path d={d} />
    </svg>
  );
}

export const ICONOS = {
  eventos: <Icono d="M8 2v4M16 2v4M3 10h18M5 4h14a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2Z" />,
  inicio: <Icono d="M3 10.5 12 3l9 7.5V20a1 1 0 0 1-1 1h-5v-6H9v6H4a1 1 0 0 1-1-1Z" />,
  reservas: <Icono d="M3 3h7v7H3zM14 3h7v7h-7zM14 14h7v7h-7zM3 14h7v7H3z" />,
  entradas: <Icono d="M3 8a2 2 0 0 0 0 4v4a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-4a2 2 0 0 0 0-4V6a2 2 0 0 0-2-2H5a2 2 0 0 0-2 2ZM13 4v2M13 10v2M13 16v2" />,
  agenda: <Icono d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2M9 11a4 4 0 1 0 0-8 4 4 0 0 0 0 8ZM23 21v-2a4 4 0 0 0-3-3.87M16 3.13a4 4 0 0 1 0 7.75" />,
  facturas: <Icono d="M4 2v20l3-2 3 2 3-2 3 2 3-2 1 .7V2l-1 .7-3-2-3 2-3-2-3 2ZM8 8h8M8 12h8M8 16h5" />,
  ayuda: <Icono d="M12 22a10 10 0 1 0 0-20 10 10 0 0 0 0 20ZM9.1 9a3 3 0 0 1 5.8 1c0 2-3 3-3 3M12 17h.01" />,
  qr: <Icono d="M3 3h6v6H3zM15 3h6v6h-6zM3 15h6v6H3zM15 15h2v2h-2zM19 15h2M15 19h2M19 19h2v2" />,
  dispositivos: <Icono d="M4 4h16v11H4zM8 20h8M12 15v5" />,
  tablero: <Icono d="M3 3v18h18M7 15l4-4 3 3 5-6" />,
  catalogo: <Icono d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20V3H6.5A2.5 2.5 0 0 0 4 5.5ZM4 19.5A2.5 2.5 0 0 0 6.5 22H20v-5" />,
  mas: <Icono d="M5 12h.01M12 12h.01M19 12h.01" />,
  alternar: <Icono d="m11 17-5-5 5-5M18 17l-5-5 5-5" />
};

function leerCompacto(): boolean {
  try {
    return localStorage.getItem("exponexo-menu") === "compacto";
  } catch {
    return false;
  }
}

export function MenuLateral({ opciones }: { opciones: OpcionMenu[] }) {
  const { pathname } = useLocation();
  const navigate = useNavigate();
  const [compacto, setCompacto] = useState(leerCompacto);
  const [primera, setPrimera] = useState(true);
  const [etiqueta, setEtiqueta] = useState<{ texto: string; top: number } | null>(null);
  const lista = useRef<HTMLElement>(null);
  const indicador = useRef<HTMLSpanElement>(null);
  const sombra = useRef<HTMLSpanElement>(null);
  const hoja = useRef<HTMLDialogElement>(null);

  const enMas = opciones.length > CASILLAS_TELEFONO ? opciones.slice(CASILLAS_TELEFONO - 1) : [];
  const activa = (to: string) => pathname === to || pathname.startsWith(`${to}/`);
  const masActiva = enMas.some((o) => activa(o.to));

  useEffect(() => {
    document.documentElement.setAttribute("data-menu", compacto ? "compacto" : "extendido");
  }, [compacto]);

  useEffect(() => {
    const t = window.setTimeout(() => setPrimera(false), 1200);
    return () => window.clearTimeout(t);
  }, []);

  const colocar = useCallback((sinAnimacion: boolean) => {
    const nav = lista.current;
    const ind = indicador.current;
    if (!nav || !ind) return;
    let objetivo = nav.querySelector<HTMLElement>('.menu-op[aria-current="page"]');
    if (!objetivo || objetivo.offsetParent === null) objetivo = masActiva ? nav.querySelector<HTMLElement>(".menu-mas") : null;
    if (!objetivo || objetivo.offsetParent === null) {
      ind.style.opacity = "0";
      return;
    }
    ind.style.opacity = "1";
    if (sinAnimacion) nav.dataset.quieto = "";
    ind.style.transform = `translate(${objetivo.offsetLeft}px, ${objetivo.offsetTop}px)`;
    ind.style.width = `${objetivo.offsetWidth}px`;
    ind.style.height = `${objetivo.offsetHeight}px`;
    if (sinAnimacion) requestAnimationFrame(() => requestAnimationFrame(() => { delete nav.dataset.quieto; }));
  }, [masActiva]);

  useLayoutEffect(() => { colocar(false); }, [pathname, compacto, colocar]);
  useEffect(() => {
    const nav = lista.current;
    if (!nav) return undefined;
    const observador = new ResizeObserver(() => colocar(true));
    observador.observe(nav);
    return () => observador.disconnect();
  }, [colocar]);

  function seguirRaton(objetivo: EventTarget) {
    const op = (objetivo as Element).closest?.<HTMLElement>(".menu-op");
    const capa = sombra.current;
    if (!op || !capa || op.closest(".menu-pie")) return;
    capa.style.transform = `translate(${op.offsetLeft}px, ${op.offsetTop}px)`;
    capa.style.width = `${op.offsetWidth}px`;
    capa.style.height = `${op.offsetHeight}px`;
    capa.dataset.listo = "";
    const caja = op.getBoundingClientRect();
    setEtiqueta({ texto: op.dataset.texto ?? "", top: caja.top + caja.height / 2 - 15 });
  }

  function alternar() {
    const siguiente = !compacto;
    setCompacto(siguiente);
    setEtiqueta(null);
    try {
      localStorage.setItem("exponexo-menu", siguiente ? "compacto" : "extendido");
    } catch {
      // sin almacenamiento
    }
  }

  function cerrarHoja() {
    const h = hoja.current;
    if (!h?.open) return;
    if (reducir()) {
      h.close();
      return;
    }
    h.dataset.cerrando = "";
    window.setTimeout(() => {
      delete h.dataset.cerrando;
      h.close();
    }, 200);
  }

  return (
    <aside className="menu-lateral" data-primera={primera ? "" : undefined}>
      <nav
        aria-label="Navegación principal"
        className="menu-nav"
        onMouseLeave={() => { sombra.current && delete sombra.current.dataset.listo; setEtiqueta(null); }}
        onMouseOver={(e) => seguirRaton(e.target)}
        ref={lista}
      >
        <span aria-hidden="true" className="menu-ind" ref={indicador} />
        <span aria-hidden="true" className="menu-hov" ref={sombra} />
        {opciones.map((o, i) => (
          <NavLink
            className={`menu-op${enMas.includes(o) ? " solo-amplio" : ""}`}
            data-texto={o.texto}
            key={o.to}
            style={{ "--k": i } as CSSProperties}
            to={o.to}
          >
            {o.icono}
            <span className="menu-texto"><span className="texto-largo">{o.texto}</span><span className="texto-corto">{o.corto ?? o.texto}</span></span>
          </NavLink>
        ))}
        {enMas.length > 0 && (
          <button
            aria-expanded={false}
            aria-haspopup="dialog"
            className={`menu-op menu-mas solo-movil${masActiva ? " contiene-actual" : ""}`}
            onClick={() => (hoja.current?.open ? cerrarHoja() : hoja.current?.showModal())}
            type="button"
          >
            {ICONOS.mas}
            <span className="menu-texto">Más</span>
          </button>
        )}
      </nav>
      <div className="menu-pie">
        <button aria-expanded={!compacto} className="menu-op menu-alternar" onClick={alternar} type="button" data-texto={compacto ? "Extender menú" : "Compactar menú"}>
          {ICONOS.alternar}
          <span className="menu-texto">{compacto ? "Extender menú" : "Compactar menú"}</span>
        </button>
      </div>
      {etiqueta && compacto && <span aria-hidden="true" className="menu-etiqueta" style={{ top: etiqueta.top }}>{etiqueta.texto}</span>}
      {enMas.length > 0 && (
        <dialog
          aria-label="Más secciones"
          className="hoja-mas"
          onCancel={(e) => { e.preventDefault(); cerrarHoja(); }}
          onClick={(e) => { if (e.target === e.currentTarget) cerrarHoja(); }}
          ref={hoja}
        >
          {enMas.map((o, i) => (
            <button
              aria-current={activa(o.to) ? "page" : undefined}
              key={o.to}
              onClick={() => { hoja.current?.close(); navigate(o.to); }}
              style={{ "--k": i } as CSSProperties}
              type="button"
            >
              {o.icono}
              {o.texto}
            </button>
          ))}
        </dialog>
      )}
    </aside>
  );
}
