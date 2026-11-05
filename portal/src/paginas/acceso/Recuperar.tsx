import React, { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { identityApi } from "../../api/clienteIdentidad";
import { CampoContrasena, contrasenaValida } from "../../componentes/CampoContrasena";
import { PanelMarca } from "../../componentes/PanelMarca";

export function Recuperar() {
  const navigate = useNavigate();
  const [paso, setPaso] = useState<1 | 2>(1);
  const [correo, setCorreo] = useState("");
  const [codigo, setCodigo] = useState("");
  const [nueva, setNueva] = useState("");
  const [confirmar, setConfirmar] = useState("");
  const [mensaje, setMensaje] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [cargando, setCargando] = useState(false);

  const pedirCodigo = async (e?: React.FormEvent) => {
    e?.preventDefault();
    setError(null);
    setCargando(true);
    try {
      const res = await identityApi.requestPasswordRecovery(correo);
      setMensaje(res.mensaje);
      setPaso(2);
    } catch (err) {
      setError(err instanceof Error ? err.message : "No se pudo enviar el código.");
    } finally {
      setCargando(false);
    }
  };

  const restablecer = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    if (!contrasenaValida(nueva)) {
      setError("La nueva contraseña no cumple todas las reglas.");
      return;
    }
    if (nueva !== confirmar) {
      setError("Las contraseñas no coinciden.");
      return;
    }
    setCargando(true);
    try {
      await identityApi.resetPassword({ correo, codigo: codigo.trim(), nueva_contrasena: nueva });
      navigate("/ingreso", { replace: true, state: { aviso: "Contraseña restablecida. Ya puedes ingresar." } });
    } catch (err) {
      setError(err instanceof Error ? err.message : "No se pudo restablecer la contraseña.");
    } finally {
      setCargando(false);
    }
  };

  return (
    <div className="login-page">
      <section className="login-panel" aria-labelledby="recuperar-title">
        <div className="login-form-content">
          <p className="login-step">Recuperar acceso <span aria-hidden="true">·</span> Paso {paso} de 2</p>
          <h1 id="recuperar-title">{paso === 1 ? "¿Olvidaste tu contraseña?" : "Crea una nueva contraseña"}</h1>
          <p className="login-description">
            {paso === 1
              ? "Escribe el correo de tu cuenta y te enviaremos un código para restablecerla."
              : "Escribe el código que llegó a tu correo y elige tu nueva contraseña. Se cerrarán tus sesiones abiertas."}
          </p>

          {error && <div className="alert alert-error" role="alert">{error}</div>}
          {mensaje && paso === 2 && <div className="alert alert-success">{mensaje}</div>}

          {paso === 1 ? (
            <form onSubmit={pedirCodigo}>
              <div className="form-group">
                <label htmlFor="correo">Correo electrónico</label>
                <input
                  id="correo"
                  className="input-field"
                  type="email"
                  autoComplete="username"
                  placeholder="nombre@correo.com"
                  maxLength={254}
                  autoFocus
                  required
                  value={correo}
                  onChange={(e) => setCorreo(e.target.value)}
                />
              </div>
              <button type="submit" className="btn btn-primary login-submit" disabled={cargando}>
                {cargando ? "Enviando…" : "Enviar código"}
              </button>
            </form>
          ) : (
            <form onSubmit={restablecer}>
              <div className="form-group">
                <label htmlFor="codigo">Código de verificación</label>
                <input
                  id="codigo"
                  className="input-field input-codigo"
                  type="text"
                  inputMode="numeric"
                  autoComplete="one-time-code"
                  maxLength={12}
                  autoFocus
                  required
                  value={codigo}
                  onChange={(e) => setCodigo(e.target.value)}
                  placeholder="123456"
                />
              </div>
              <CampoContrasena id="nueva" etiqueta="Nueva contraseña" valor={nueva} alCambiar={setNueva} autoComplete="new-password" conMedidor />
              <CampoContrasena id="confirmar" etiqueta="Confirmar nueva contraseña" valor={confirmar} alCambiar={setConfirmar} autoComplete="new-password" />
              <button type="submit" className="btn btn-primary login-submit" disabled={cargando}>
                {cargando ? "Guardando…" : "Restablecer contraseña"}
              </button>
              <button type="button" className="btn-enlace" onClick={() => void pedirCodigo()} disabled={cargando}>
                Enviar otro código
              </button>
            </form>
          )}

          <p className="login-register">
            ¿La recordaste? <Link to="/ingreso">Volver al ingreso</Link>
          </p>
        </div>
        <p className="login-panel-footer">El código vence en pocos minutos y sirve una sola vez.</p>
      </section>

      <PanelMarca eyebrow="Acceso protegido" titulo="Recupera tu acceso en minutos." texto="Verificamos que eres tú con un código de un solo uso enviado a tu correo." />
    </div>
  );
}
