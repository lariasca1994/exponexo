import React, { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { identityApi } from "../../api/clienteIdentidad";

export function Registro() {
  const navigate = useNavigate();
  const [nombre, setNombre] = useState("");
  const [correo, setCorreo] = useState("");
  const [contrasena, setContrasena] = useState("");
  const [rol, setRol] = useState<"visitante" | "expositor">("visitante");
  const [error, setError] = useState<string | null>(null);
  const [exito, setExito] = useState(false);
  const [cargando, setCargando] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setCargando(true);
    try {
      await identityApi.registerAccount({ correo, nombre, contrasena, rol });
      setExito(true);
      setTimeout(() => navigate("/ingreso"), 1800);
    } catch (err) {
      setError(err instanceof Error ? err.message : "No se pudo completar el registro.");
    } finally {
      setCargando(false);
    }
  };

  return (
    <div className="auth-wrapper">
      <div className="auth-card">
        <h2 style={{ marginTop: 0 }}>Crear cuenta en ExpoNexo</h2>
        <p style={{ color: "var(--text-secondary)", fontSize: "0.92rem" }}>
          Todas las cuentas cuentan con verificación en dos pasos desde el primer ingreso.
        </p>

        {error && <div className="alert alert-error">{error}</div>}
        {exito && (
          <div className="alert alert-success">
            Cuenta creada correctamente. Redirigiendo al ingreso…
          </div>
        )}

        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label htmlFor="nombre">Nombre completo</label>
            <input
              id="nombre"
              className="input-field"
              type="text"
              required
              minLength={2}
              value={nombre}
              onChange={(e) => setNombre(e.target.value)}
            />
          </div>

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
            <label htmlFor="rol">Tipo de participación</label>
            <select
              id="rol"
              className="select-field"
              value={rol}
              onChange={(e) => setRol(e.target.value as "visitante" | "expositor")}
            >
              <option value="visitante">Visitante (entradas y agenda de citas)</option>
              <option value="expositor">Expositor (reserva de stands y citas)</option>
            </select>
          </div>

          <div className="form-group">
            <label htmlFor="contrasena">Contraseña</label>
            <input
              id="contrasena"
              className="input-field"
              type="password"
              required
              minLength={10}
              placeholder="Mínimo 10 caracteres, mayúscula, número y símbolo"
              value={contrasena}
              onChange={(e) => setContrasena(e.target.value)}
            />
          </div>

          <button type="submit" className="btn btn-primary" style={{ width: "100%" }} disabled={cargando}>
            {cargando ? "Registrando…" : "Registrarme"}
          </button>
        </form>

        <p style={{ marginTop: "1.2rem", fontSize: "0.9rem", textAlign: "center" }}>
          ¿Ya tienes cuenta? <Link to="/ingreso">Ingresa aquí</Link>
        </p>
      </div>
    </div>
  );
}
