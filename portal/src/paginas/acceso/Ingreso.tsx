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
    <div className="auth-wrapper">
      <div className="auth-card">
        <h2 style={{ marginTop: 0 }}>Ingresar a ExpoNexo</h2>
        <p style={{ color: "var(--text-secondary)", fontSize: "0.92rem" }}>
          Paso 1 de 2: ingresa tu correo y contraseña para continuar al segundo factor.
        </p>

        {error && <div className="alert alert-error">{error}</div>}

        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label htmlFor="correo">Correo electrónico</label>
            <input
              id="correo"
              className="input-field"
              type="email"
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
              required
              value={contrasena}
              onChange={(e) => setContrasena(e.target.value)}
            />
          </div>

          <button type="submit" className="btn btn-primary" style={{ width: "100%" }} disabled={cargando}>
            {cargando ? "Verificando…" : "Continuar al segundo paso"}
          </button>
        </form>

        <p style={{ marginTop: "1.2rem", fontSize: "0.9rem", textAlign: "center" }}>
          ¿Aún no tienes cuenta? <Link to="/registro">Regístrate</Link>
        </p>
      </div>
    </div>
  );
}
