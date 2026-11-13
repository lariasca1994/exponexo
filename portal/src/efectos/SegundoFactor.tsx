import { useEffect, useState } from "react";

// Piezas del paso del código (segundo factor): candado, casillas y anillo de tiempo.

export type EstadoCandado = "normal" | "verificando" | "abierto" | "error";

/** Candado sobre el título: flota; se abre con el código correcto y se sacude con uno equivocado. */
export function Candado({ estado = "normal" }: { estado?: EstadoCandado }) {
  return (
    <span className="candado" data-estado={estado} aria-hidden="true">
      <svg viewBox="0 0 48 48">
        <path className="arco" d="M15 22v-7a9 9 0 0 1 18 0v7" />
        <rect className="cuerpo" x="9" y="21" width="30" height="21" rx="6" />
        <circle className="ojo" cx="24" cy="31.5" r="3.4" />
      </svg>
    </span>
  );
}

/**
 * Seis casillas dibujadas encima del mismo <input> (mismo id, etiqueta y autocompletado):
 * solo muestran los dígitos escritos. Con `error` el grupo tiembla.
 */
export function VistaCasillas({ valor, foco, error = false }: { valor: string; foco: boolean; error?: boolean }) {
  const digitos = valor.replace(/\D/g, "").slice(0, 6);
  const [pulso, setPulso] = useState(-1);
  const [anterior, setAnterior] = useState(digitos);
  if (digitos !== anterior) {
    setAnterior(digitos);
    setPulso(digitos.length > anterior.length ? digitos.length - 1 : -1);
  }
  useEffect(() => {
    if (pulso < 0) return undefined;
    const t = window.setTimeout(() => setPulso(-1), 300);
    return () => window.clearTimeout(t);
  }, [pulso]);
  return (
    <div className={`casillas-vista${error ? " error" : ""}${digitos.length === 6 ? " completa" : ""}`} aria-hidden="true">
      {Array.from({ length: 6 }, (_, i) => (
        <span
          className={[digitos[i] ? "llena" : "", foco && i === Math.min(digitos.length, 5) ? "activa" : "", pulso === i ? "pulso" : ""].join(" ")}
          key={i}
        >
          {digitos[i] ?? ""}
        </span>
      ))}
    </div>
  );
}

/** Cuánto falta para que la app autenticadora muestre otro código (cambian cada 30 s). */
export function AnilloApp() {
  const faltan = () => 30 - (Math.floor(Date.now() / 1000) % 30);
  const [resto, setResto] = useState(faltan);
  useEffect(() => {
    const t = window.setInterval(() => setResto(faltan()), 1000);
    return () => window.clearInterval(t);
  }, []);
  return (
    <p className={`anillo${resto <= 5 ? " urgente" : ""}`}>
      <svg viewBox="0 0 24 24" aria-hidden="true">
        <circle className="anillo-fondo" cx="12" cy="12" r="9" />
        <circle className="anillo-valor" cx="12" cy="12" r="9" pathLength={1} style={{ strokeDashoffset: 1 - resto / 30 }} />
      </svg>
      <span>Tu app muestra un código nuevo en {resto} s</span>
    </p>
  );
}
