import { useEffect, useState } from "react";

// Panel de marca animado de las pantallas de acceso: el motivo del proyecto es el plano de un
// pabellón. Los stands se reservan (se encienden con los colores de las tres bases), un visitante
// recorre los pasillos y su entrada QR se valida al llegar. Sin movimiento si el sistema lo pide.

const STANDS = [
  { x: 24, y: 24, w: 52, h: 38, c: "sql" },
  { x: 84, y: 24, w: 52, h: 38, c: "ora" },
  { x: 144, y: 24, w: 76, h: 38, c: "mdb" },
  { x: 228, y: 24, w: 52, h: 38, c: "sql" },
  { x: 24, y: 104, w: 52, h: 52, c: "mdb" },
  { x: 84, y: 104, w: 76, h: 52, c: "sql" },
  { x: 168, y: 104, w: 52, h: 52, c: "ora" },
  { x: 228, y: 104, w: 52, h: 52, c: "mdb" },
  { x: 24, y: 196, w: 76, h: 38, c: "ora" },
  { x: 108, y: 196, w: 52, h: 38, c: "mdb" },
  { x: 168, y: 196, w: 52, h: 38, c: "sql" },
  { x: 228, y: 196, w: 52, h: 38, c: "ora" }
];

interface Props {
  eyebrow?: string;
  titulo?: string;
  texto?: string;
}

function useMovimiento(): boolean {
  const [permitido, setPermitido] = useState(
    () => typeof window === "undefined" || !window.matchMedia("(prefers-reduced-motion: reduce)").matches
  );
  useEffect(() => {
    const consulta = window.matchMedia("(prefers-reduced-motion: reduce)");
    const cambiar = () => setPermitido(!consulta.matches);
    consulta.addEventListener("change", cambiar);
    return () => consulta.removeEventListener("change", cambiar);
  }, []);
  return permitido;
}

export function PanelMarca({
  eyebrow = "Ferias que conectan",
  titulo = "Todo tu evento, en un solo lugar.",
  texto = "ExpoNexo reúne a quienes organizan, exponen y visitan para que cada encuentro cuente."
}: Props) {
  const movimiento = useMovimiento();
  return (
    <aside className="login-story" aria-labelledby="login-story-title">
      <div className="login-story-orbit login-story-orbit-one" aria-hidden="true" />
      <div className="login-story-orbit login-story-orbit-two" aria-hidden="true" />
      <div className="login-story-content">
        <span className="login-story-eyebrow">{eyebrow}</span>
        <h2 id="login-story-title">{titulo}</h2>
        <p>{texto}</p>
      </div>

      <div className="plano-animado" aria-hidden="true">
        <svg viewBox="0 0 304 258" className="plano-svg">
          <rect x="8" y="8" width="288" height="242" rx="14" className="plano-recinto" />
          {/* Pasillos */}
          <path d="M16 83 H288 M16 175 H288 M80 70 V188 M164 70 V188 M224 70 V188" className="plano-pasillo" />
          {STANDS.map((s, i) => (
            <rect
              key={i}
              x={s.x}
              y={s.y}
              width={s.w}
              height={s.h}
              rx="5"
              className={`plano-stand plano-${s.c}`}
              style={{ animationDelay: `${0.6 + i * 0.32}s` }}
            />
          ))}
          {/* Recorrido del visitante y su entrada validada */}
          <path id="ruta-visitante" d="M16 83 H80 V175 H164 V83 H224 V175 H288" className="plano-ruta" />
          <g transform={movimiento ? undefined : "translate(288 175)"}>
            <circle r="11" className="plano-visitante-eco" />
            <circle r="6" className="plano-visitante" />
            {movimiento && (
              <animateMotion dur="9s" begin="1s" repeatCount="indefinite" keyPoints="0;1;1" keyTimes="0;0.8;1" calcMode="linear">
                <mpath href="#ruta-visitante" />
              </animateMotion>
            )}
          </g>
        </svg>

        <div className="qr-validacion">
          <svg viewBox="0 0 21 21" className="qr-mini">
            <path d="M0 0h7v7H0zM14 0h7v7h-7zM0 14h7v7H0z" className="qr-ancla" />
            <path d="M2 2h3v3H2zM16 2h3v3h-3zM2 16h3v3H2z" className="qr-centro" />
            <path d="M9 1h2v2H9zM9 5h3v2H9zM8 9h2v2H8zM12 8h2v3h-2zM15 9h3v2h-3zM9 12h2v3H9zM13 13h3v2h-3zM17 13h3v4h-3zM9 17h3v3H9zM13 17h2v3h-2z" className="qr-modulos" />
          </svg>
          <span className="qr-linea" />
          <span className="qr-estado">
            <strong>Entrada validada</strong>
            Pabellón 2 · Puerta norte
          </span>
        </div>
      </div>

      <div className="login-story-footer">
        <span>Expositores</span>
        <span aria-hidden="true">·</span>
        <span>Visitantes</span>
        <span aria-hidden="true">·</span>
        <span>Organizadores</span>
      </div>
    </aside>
  );
}
