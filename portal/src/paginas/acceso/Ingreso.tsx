import React, { useState } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";
import { identityApi } from "../../api/clienteIdentidad";
import { CampoContrasena } from "../../componentes/CampoContrasena";
import { PanelMarca } from "../../componentes/PanelMarca";
import { llavesDisponibles, usarLlave } from "../../sesion/llavesAcceso";
import { useSession } from "../../sesion/almacenSesion";

export function Ingreso() {
  const navigate = useNavigate();
  const aviso = (useLocation().state as { aviso?: string } | null)?.aviso;
  const { savePendingMfa, establishSession } = useSession();
  const [correo, setCorreo] = useState("");
  const [contrasena, setContrasena] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [cargando, setCargando] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setCargando(true);
    try {
      const step1 = await identityApi.loginStep1({ correo, contrasena });
      savePendingMfa(correo, step1);
      navigate("/segundo-paso");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Error al verificar las credenciales.");
    } finally {
      setCargando(false);
    }
  };

  const ingresarConLlave = async () => {
    setError(null);
    if (!correo) {
      setError("Escribe tu correo para buscar tus llaves de acceso.");
      return;
    }
    setCargando(true);
    try {
      const { opciones, desafio_token } = await identityApi.passkeyLoginOptions(correo);
      const credencial = await usarLlave(opciones);
      establishSession(await identityApi.passkeyLogin({ correo, desafio_token, credencial }));
      navigate("/inicio");
    } catch (err) {
      setError(
        err instanceof DOMException
          ? "Se canceló el uso de la llave de acceso."
          : err instanceof Error
            ? err.message
            : "No se pudo ingresar con la llave de acceso."
      );
    } finally {
      setCargando(false);
    }
  };

  return (
    <div className="login-page">
      <section className="login-panel" aria-labelledby="login-title">
        <div className="login-form-content">
          <p className="login-step">Acceso seguro <span aria-hidden="true">·</span> Paso 1 de 2</p>
          <h1 id="login-title">Qué bueno tenerte de vuelta</h1>
          <p className="login-description">
            Ingresa a tu cuenta para continuar con tus eventos, reservas y encuentros de negocio.
          </p>

          {aviso && !error && <div className="alert alert-success" role="status">{aviso}</div>}
          {error && <div className="alert alert-error" role="alert">{error}</div>}

          <form onSubmit={handleSubmit}>
            <div className="form-group">
              <label htmlFor="correo">Correo electrónico</label>
              <input
                id="correo"
                className="input-field"
                type="email"
                name="correo"
                autoComplete="username webauthn"
                placeholder="nombre@correo.com"
                maxLength={254}
                autoFocus
                required
                value={correo}
                onChange={(e) => setCorreo(e.target.value)}
              />
            </div>

            <CampoContrasena
              id="contrasena"
              etiqueta="Contraseña"
              valor={contrasena}
              alCambiar={setContrasena}
              autoComplete="current-password"
            />

            <div className="login-fila-ayuda">
              <span className="login-security-note">Luego verificaremos tu segundo factor.</span>
              <Link to="/recuperar" className="login-olvido">¿Olvidaste tu contraseña?</Link>
            </div>

            <button type="submit" className="btn btn-primary login-submit" disabled={cargando}>
              {cargando ? "Verificando…" : "Continuar"}
            </button>
          </form>

          {llavesDisponibles() && (
            <>
              <div className="login-separador"><span>o</span></div>
              <button type="button" className="btn btn-secondary login-llave" onClick={ingresarConLlave} disabled={cargando}>
                <svg viewBox="0 0 24 24" width="18" height="18" aria-hidden="true" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
                  <circle cx="8" cy="15" r="4" />
                  <path d="M11 12l9-9M17 6l3 3M14 9l2 2" />
                </svg>
                Ingresar con llave de acceso
              </button>
            </>
          )}

          <p className="login-register">
            ¿Aún no tienes cuenta? <Link to="/registro">Crea tu cuenta</Link>
          </p>
        </div>

        <p className="login-panel-footer">Tu próxima oportunidad de negocio comienza aquí.</p>
      </section>

      <PanelMarca />
    </div>
  );
}
