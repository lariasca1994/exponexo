import React, { useState } from "react";
import { Navigate, useNavigate } from "react-router-dom";
import { identityApi } from "../../api/clienteIdentidad";
import { useSession } from "../../sesion/almacenSesion";

export function SegundoPaso() {
  const navigate = useNavigate();
  const { pendingMfa, establishSession } = useSession();

  const [metodo, setMetodo] = useState<"app" | "correo" | "respaldo">(
    (pendingMfa?.metodo_preferido as "app" | "correo") || "correo"
  );
  const [codigo, setCodigo] = useState("");
  const [mensaje, setMensaje] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [cargando, setCargando] = useState(false);

  if (!pendingMfa) {
    return <Navigate to="/ingreso" replace />;
  }

  const handleEnviarCodigoCorreo = async () => {
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
    try {
      const tokens = await identityApi.loginStep2(pendingMfa.pase_segundo_paso, {
        metodo,
        codigo
      });
      establishSession(tokens);
      navigate("/inicio");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Código de verificación inválido.");
    } finally {
      setCargando(false);
    }
  };

  return (
    <div className="auth-wrapper">
      <div className="auth-card">
        <h2 style={{ marginTop: 0 }}>Verificación en dos pasos</h2>
        <p style={{ color: "var(--text-secondary)", fontSize: "0.92rem" }}>
          Cuenta: <strong>{pendingMfa.correo}</strong>
        </p>

        {error && <div className="alert alert-error">{error}</div>}
        {mensaje && <div className="alert alert-success">{mensaje}</div>}

        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label htmlFor="metodo">Método de verificación</label>
            <select
              id="metodo"
              className="select-field"
              value={metodo}
              onChange={(e) => setMetodo(e.target.value as "app" | "correo" | "respaldo")}
            >
              {pendingMfa.metodos_disponibles.includes("app") && (
                <option value="app">Aplicación autenticadora (TOTP)</option>
              )}
              <option value="correo">Código enviado por correo</option>
              <option value="respaldo">Código de respaldo de un solo uso</option>
            </select>
          </div>

          {metodo === "correo" && (
            <div style={{ marginBottom: "1rem" }}>
              <button
                type="button"
                className="btn btn-secondary"
                style={{ width: "100%" }}
                onClick={handleEnviarCodigoCorreo}
              >
                Enviar código a mi correo
              </button>
            </div>
          )}

          <div className="form-group">
            <label htmlFor="codigo">
              {metodo === "respaldo" ? "Código de respaldo (XXXX-XXXX)" : "Código de 6 dígitos"}
            </label>
            <input
              id="codigo"
              className="input-field"
              type="text"
              required
              value={codigo}
              onChange={(e) => setCodigo(e.target.value)}
              placeholder={metodo === "respaldo" ? "A1B2-C3D4" : "123456"}
            />
          </div>

          <button type="submit" className="btn btn-primary" style={{ width: "100%" }} disabled={cargando}>
            {cargando ? "Verificando código…" : "Confirmar e ingresar"}
          </button>
        </form>
      </div>
    </div>
  );
}
