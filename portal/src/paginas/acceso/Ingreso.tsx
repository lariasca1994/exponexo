import React, { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { identityApi } from "../../api/clienteIdentidad";
import { useSession } from "../../sesion/almacenSesion";

export function Ingreso() {
  const navigate = useNavigate();
  const { savePendingMfa } = useSession();
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

  return (
    <div className="login-page">
      <section className="login-panel" aria-labelledby="login-title">
        <div className="login-form-content">
          <p className="login-step">Acceso seguro <span aria-hidden="true">·</span> Paso 1 de 2</p>
          <h1 id="login-title">Qué bueno tenerte de vuelta</h1>
          <p className="login-description">
            Ingresa a tu cuenta para continuar con tus eventos, reservas y encuentros de negocio.
          </p>

          {error && <div className="alert alert-error" role="alert">{error}</div>}

          <form onSubmit={handleSubmit}>
            <div className="form-group">
              <label htmlFor="correo">Correo electrónico</label>
              <input
                id="correo"
                className="input-field"
                type="email"
                name="correo"
                autoComplete="username"
                placeholder="nombre@correo.com"
                maxLength={254}
                autoFocus
                required
                value={correo}
                onChange={(e) => setCorreo(e.target.value)}
              />
            </div>

            <div className="form-group">
              <label htmlFor="contrasena">Contraseña</label>
              <input
                id="contrasena"
                className="input-field"
                type="password"
                name="contrasena"
                autoComplete="current-password"
                required
                value={contrasena}
                onChange={(e) => setContrasena(e.target.value)}
              />
            </div>

            <p className="login-security-note">
              Después verificaremos tu segundo factor para proteger tu cuenta.
            </p>
            <button type="submit" className="btn btn-primary login-submit" disabled={cargando}>
              {cargando ? "Verificando…" : "Continuar"}
            </button>
          </form>

          <p className="login-register">
            ¿Aún no tienes cuenta? <Link to="/registro">Crea tu cuenta</Link>
          </p>
        </div>

        <p className="login-panel-footer">Tu próxima oportunidad de negocio comienza aquí.</p>
      </section>

      <aside className="login-story" aria-labelledby="login-story-title">
        <div className="login-story-orbit login-story-orbit-one" aria-hidden="true" />
        <div className="login-story-orbit login-story-orbit-two" aria-hidden="true" />
        <div className="login-story-content">
          <span className="login-story-eyebrow">Ferias que conectan</span>
          <h2 id="login-story-title">Todo tu evento, en un solo lugar.</h2>
          <p>
            ExpoNexo reúne a quienes organizan, exponen y visitan para que cada encuentro cuente.
          </p>

          <ul className="login-benefits">
            <li>
              <span className="login-benefit-icon" aria-hidden="true">01</span>
              <span><strong>Gestiona tu presencia</strong>Explora eventos y reserva stands.</span>
            </li>
            <li>
              <span className="login-benefit-icon" aria-hidden="true">02</span>
              <span><strong>Entra con confianza</strong>Consulta tus entradas y códigos QR.</span>
            </li>
            <li>
              <span className="login-benefit-icon" aria-hidden="true">03</span>
              <span><strong>Conecta con propósito</strong>Organiza reuniones y sigue tus actividades.</span>
            </li>
          </ul>
        </div>
        <div className="login-story-footer">
          <span>Expositores</span><span aria-hidden="true">·</span>
          <span>Visitantes</span><span aria-hidden="true">·</span>
          <span>Organizadores</span>
        </div>
      </aside>
    </div>
  );
}
