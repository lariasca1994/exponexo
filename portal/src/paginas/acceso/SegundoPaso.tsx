import React, { useRef, useState } from "react";
import { Link, Navigate, useNavigate } from "react-router-dom";
import { identityApi } from "../../api/clienteIdentidad";
import { PanelMarca } from "../../componentes/PanelMarca";
import { useSession } from "../../sesion/almacenSesion";
import { AnilloApp, Candado, VistaCasillas, type EstadoCandado } from "../../efectos/SegundoFactor";

type Metodo = "app" | "correo" | "respaldo";

const ETIQUETAS: Record<Metodo, string> = {
  app: "App autenticadora",
  correo: "Código por correo",
  respaldo: "Código de respaldo"
};

export function SegundoPaso() {
  const navigate = useNavigate();
  const { pendingMfa, establishSession } = useSession();
  const [metodo, setMetodo] = useState<Metodo>((pendingMfa?.metodo_preferido as Metodo) || "correo");
  const [codigo, setCodigo] = useState("");
  const [mensaje, setMensaje] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [cargando, setCargando] = useState(false);
  // Solo presentación: candado y casillas del código.
  const [candado, setCandado] = useState<EstadoCandado>("normal");
  const [foco, setFoco] = useState(false);
  // Al validar el código, establishSession borra pendingMfa: sin esta marca, la redirección a
  // /ingreso de abajo le ganaba a navigate("/inicio") y la persona terminaba en el ingreso.
  const verificado = useRef(false);

  if (!pendingMfa) {
    return verificado.current ? null : <Navigate to="/ingreso" replace />;
  }

  const metodos: Metodo[] = [
    ...(pendingMfa.metodos_disponibles.includes("app") ? (["app"] as Metodo[]) : []),
    "correo",
    "respaldo"
  ];

  const enviarCodigoCorreo = async () => {
    setError(null);
    setMensaje(null);
    try {
      const res = await identityApi.requestLoginEmailCode(pendingMfa.pase_segundo_paso);
      setMensaje(res.mensaje);
    } catch (err) {
      setError(err instanceof Error ? err.message : "No se pudo enviar el código por correo.");
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setCargando(true);
    setCandado("verificando");
    try {
      const tokens = await identityApi.loginStep2(pendingMfa.pase_segundo_paso, { metodo, codigo: codigo.trim() });
      // El candado se abre un momento antes de entrar.
      setCandado("abierto");
      if (!window.matchMedia("(prefers-reduced-motion: reduce)").matches) {
        await new Promise((resolver) => window.setTimeout(resolver, 450));
      }
      verificado.current = true;
      establishSession(tokens);
      navigate("/inicio");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Código de verificación inválido.");
      setCandado("error");
      window.setTimeout(() => setCandado("normal"), 700);
    } finally {
      setCargando(false);
    }
  };

  return (
    <div className="login-page">
      <section className="login-panel" aria-labelledby="mfa-title">
        <div className="login-form-content">
          <Candado estado={candado} />
          <p className="login-step">Acceso seguro <span aria-hidden="true">·</span> Paso 2 de 2</p>
          <h1 id="mfa-title">Verifica que eres tú</h1>
          <p className="login-description">
            Cuenta <strong>{pendingMfa.correo}</strong>. Elige cómo confirmar tu identidad.
          </p>

          {error && <div className="alert alert-error" role="alert">{error}</div>}
          {mensaje && <div className="alert alert-success">{mensaje}</div>}

          <div className="selector-metodo" role="radiogroup" aria-label="Método de verificación">
            {metodos.map((m) => (
              <button
                key={m}
                type="button"
                role="radio"
                aria-checked={metodo === m}
                className={metodo === m ? "activo" : ""}
                onClick={() => {
                  setMetodo(m);
                  setCodigo("");
                }}
              >
                {ETIQUETAS[m]}
              </button>
            ))}
          </div>

          <form onSubmit={handleSubmit}>
            {metodo === "correo" && (
              <button type="button" className="btn btn-secondary login-submit" onClick={enviarCodigoCorreo}>
                Enviar código a mi correo
              </button>
            )}
            <div className="form-group" style={{ marginTop: "var(--esp-4)" }}>
              <label htmlFor="codigo">{metodo === "respaldo" ? "Código de respaldo (XXXX-XXXX)" : "Código de 6 dígitos"}</label>
              {/* Con 6 dígitos (app o correo) el mismo campo se ve como seis casillas. */}
              <div className={metodo === "respaldo" ? undefined : "casillas-codigo"}>
                <input
                  id="codigo"
                  className="input-field input-codigo"
                  type="text"
                  inputMode={metodo === "respaldo" ? "text" : "numeric"}
                  autoComplete="one-time-code"
                  maxLength={16}
                  required
                  autoFocus
                  value={codigo}
                  onBlur={() => setFoco(false)}
                  onChange={(e) => setCodigo(e.target.value)}
                  onFocus={() => setFoco(true)}
                  placeholder={metodo === "respaldo" ? "A1B2-C3D4" : "123456"}
                />
                {metodo !== "respaldo" && <VistaCasillas valor={codigo} foco={foco} error={candado === "error"} />}
              </div>
              {metodo === "app" && <AnilloApp />}
            </div>
            <button type="submit" className="btn btn-primary login-submit" disabled={cargando}>
              {cargando ? "Verificando…" : "Confirmar e ingresar"}
            </button>
          </form>

          <p className="login-register">
            ¿No eres tú? <Link to="/ingreso">Volver al ingreso</Link>
          </p>
        </div>
        <p className="login-panel-footer">La verificación en dos pasos es obligatoria en todas las cuentas.</p>
      </section>

      <PanelMarca eyebrow="Acceso protegido" titulo="Un paso más y estás dentro." texto="Tu segundo factor protege tus reservas, pagos y entradas aunque alguien conozca tu contraseña." />
    </div>
  );
}
