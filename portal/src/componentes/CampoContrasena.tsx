import { useId, useState } from "react";

// Reglas de la política de contraseñas (las mismas que valida el servidor)
const REGLAS: { texto: string; cumple: (v: string) => boolean }[] = [
  { texto: "10 caracteres", cumple: (v) => v.length >= 10 },
  { texto: "Mayúscula", cumple: (v) => /[A-Z]/.test(v) },
  { texto: "Minúscula", cumple: (v) => /[a-z]/.test(v) },
  { texto: "Número", cumple: (v) => /\d/.test(v) },
  { texto: "Símbolo", cumple: (v) => /[^A-Za-z0-9]/.test(v) }
];

export function contrasenaValida(valor: string): boolean {
  return REGLAS.every((r) => r.cumple(valor));
}

interface Props {
  id: string;
  etiqueta: string;
  valor: string;
  alCambiar: (valor: string) => void;
  autoComplete: "current-password" | "new-password";
  conMedidor?: boolean;
  autoFocus?: boolean;
}

export function CampoContrasena({ id, etiqueta, valor, alCambiar, autoComplete, conMedidor, autoFocus }: Props) {
  const [visible, setVisible] = useState(false);
  const ayudaId = useId();
  const cumplidas = REGLAS.filter((r) => r.cumple(valor)).length;
  const nivel = valor ? (cumplidas <= 2 ? "debil" : cumplidas < REGLAS.length ? "media" : "fuerte") : "vacia";

  return (
    <div className="form-group">
      <label htmlFor={id}>{etiqueta}</label>
      <div className="campo-contrasena">
        <input
          id={id}
          name={id}
          className="input-field"
          type={visible ? "text" : "password"}
          autoComplete={autoComplete}
          autoFocus={autoFocus}
          required
          maxLength={128}
          value={valor}
          onChange={(e) => alCambiar(e.target.value)}
          aria-describedby={conMedidor ? ayudaId : undefined}
        />
        <button
          type="button"
          className="campo-contrasena-ojo"
          onClick={() => setVisible((v) => !v)}
          aria-label={visible ? "Ocultar contraseña" : "Mostrar contraseña"}
          aria-pressed={visible}
        >
          <svg viewBox="0 0 24 24" width="20" height="20" aria-hidden="true" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
            <path d="M2 12s3.6-7 10-7 10 7 10 7-3.6 7-10 7S2 12 2 12Z" />
            <circle cx="12" cy="12" r="3" />
            {visible && <path d="M4 4l16 16" />}
          </svg>
        </button>
      </div>
      {conMedidor && (
        <div id={ayudaId} className={`medidor-contrasena medidor-${nivel}`} aria-live="polite">
          <div className="medidor-barras" aria-hidden="true">
            {REGLAS.map((r, i) => (
              <span key={r.texto} className={i < cumplidas ? "llena" : ""} />
            ))}
          </div>
          <ul>
            {REGLAS.map((r) => (
              <li key={r.texto} className={r.cumple(valor) ? "cumple" : ""}>
                {r.texto}
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
