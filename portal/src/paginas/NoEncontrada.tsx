import type { CSSProperties } from "react";
import { Link, useLocation } from "react-router-dom";
import { useSession } from "../sesion/almacenSesion";

// 404 propio: el plano del pabellón con un stand marcado que no existe. "Stand 404 · sin asignar".
const STANDS = [
  [24, 24, 52, 38], [84, 24, 52, 38], [144, 24, 76, 38], [228, 24, 52, 38],
  [24, 104, 52, 52], [84, 104, 76, 52], [228, 104, 52, 52],
  [24, 196, 76, 38], [108, 196, 52, 38], [168, 196, 52, 38], [228, 196, 52, 38]
];

export function NoEncontrada() {
  const { pathname } = useLocation();
  const { user } = useSession();
  return (
    <section className="no-encontrada">
      <div className="no-encontrada__plano" aria-hidden="true">
        <svg viewBox="0 0 304 258">
          <rect x="8" y="8" width="288" height="242" rx="14" className="plano-recinto" />
          <path d="M16 83 H288 M16 175 H288 M80 70 V188 M164 70 V188 M224 70 V188" className="plano-pasillo" />
          {STANDS.map(([x, y, w, h], i) => (
            <rect key={i} x={x} y={y} width={w} height={h} rx="5" className="no-encontrada__stand" style={{ "--i": i } as CSSProperties} />
          ))}
          <rect x="168" y="104" width="52" height="52" rx="5" className="no-encontrada__vacio" />
          <text x="194" y="135" textAnchor="middle" className="no-encontrada__numero">404</text>
        </svg>
        <p><span>Stand 404</span><strong>sin asignar</strong></p>
      </div>
      <div className="no-encontrada__texto">
        <p className="no-encontrada__eyebrow">Página no encontrada</p>
        <h1>Este stand no está en el plano</h1>
        <p>
          Buscamos <code>{pathname}</code> en el recinto y ninguna pantalla responde ahí.
          {user ? " Tu sesión sigue abierta." : ""}
        </p>
        <div className="no-encontrada__acciones">
          <Link className="btn btn-primary" to="/eventos">Ver eventos</Link>
          <Link className="btn btn-secondary" to={user ? "/inicio" : "/"}>Volver al inicio</Link>
        </div>
      </div>
    </section>
  );
}
