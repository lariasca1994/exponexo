import React, { useEffect, useState } from "react";
import { identityApi } from "../../api/clienteIdentidad";
import type { SecurityProfileResponse, TotpSetupResponse } from "../../tipos/identidad";

export function SeguridadPerfil() {
  const [perfil, setPerfil] = useState<SecurityProfileResponse | null>(null);
  const [totpSetup, setTotpSetup] = useState<TotpSetupResponse | null>(null);
  const [codigoTotp, setCodigoTotp] = useState("");
  const [codigosRespaldo, setCodigosRespaldo] = useState<string[] | null>(null);
  const [mensaje, setMensaje] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [cargando, setCargando] = useState(true);

  const cargarPerfil = async () => {
    setCargando(true);
    try {
      const data = await identityApi.getSecurityProfile();
      setPerfil(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "No se pudo cargar el perfil de seguridad.");
    } finally {
      setCargando(false);
    }
  };

  useEffect(() => {
    void cargarPerfil();
  }, []);

  const handleIniciarTotp = async () => {
    setError(null);
    setMensaje(null);
    try {
      const setup = await identityApi.startTotpSetup();
      setTotpSetup(setup);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Error al iniciar configuración TOTP.");
    }
  };

  const handleConfirmarTotp = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setMensaje(null);
    try {
      const actualizado = await identityApi.confirmTotpSetup(codigoTotp);
      setPerfil(actualizado);
      setTotpSetup(null);
      setCodigoTotp("");
      setMensaje("Aplicación autenticadora activada y definida como método preferido.");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Código TOTP incorrecto.");
    }
  };

  const handleGenerarRespaldo = async () => {
    setError(null);
    setMensaje(null);
    try {
      const res = await identityApi.generateBackupCodes();
      setCodigosRespaldo(res.codigos);
      await cargarPerfil();
      setMensaje("Se generaron 8 nuevos códigos de respaldo de un solo uso.");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Error al generar códigos de respaldo.");
    }
  };

  const handleCambiarPreferido = async (tipo: "app" | "correo") => {
    setError(null);
    try {
      const actualizado = await identityApi.setPreferredMfa(tipo);
      setPerfil(actualizado);
      setMensaje(`Método preferido actualizado a: ${tipo}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "No se pudo cambiar el método preferido.");
    }
  };

  if (cargando && !perfil) {
    return (
      <div className="container">
        <div className="panel-card">Cargando configuración de seguridad…</div>
      </div>
    );
  }

  return (
    <div className="container">
      <h1 style={{ marginTop: 0 }}>Seguridad del perfil</h1>

      {error && <div className="alert alert-error">{error}</div>}
      {mensaje && <div className="alert alert-success">{mensaje}</div>}

      <div className="grid-2">
        <div className="panel-card">
          <h3>Aplicación autenticadora (TOTP)</h3>
          <p style={{ color: "var(--text-secondary)", fontSize: "0.92rem" }}>
            Escanea el código QR con Google Authenticator, Microsoft Authenticator o Authy e ingresa
            el primer código de 6 dígitos para activarla.
          </p>

          {!totpSetup ? (
            <button type="button" className="btn btn-primary" onClick={handleIniciarTotp}>
              Configurar aplicación autenticadora (QR)
            </button>
          ) : (
            <div>
              <img
                src={totpSetup.qr_datos_url}
                alt="Código QR para app autenticadora"
                className="qr-preview"
              />
              <p style={{ fontSize: "0.85rem", wordBreak: "break-all" }}>
                Clave manual: <code>{totpSetup.secreto}</code>
              </p>
              <form onSubmit={handleConfirmarTotp}>
                <div className="form-group">
                  <label htmlFor="codigo-totp">Primer código de 6 dígitos</label>
                  <input
                    id="codigo-totp"
                    className="input-field"
                    type="text"
                    required
                    maxLength={6}
                    value={codigoTotp}
                    onChange={(e) => setCodigoTotp(e.target.value)}
                    placeholder="123456"
                  />
                </div>
                <button type="submit" className="btn btn-primary">
                  Confirmar y activar app
                </button>
              </form>
            </div>
          )}
        </div>

        <div className="panel-card">
          <h3>Métodos activos y códigos de respaldo</h3>
          {perfil && (
            <ul style={{ paddingLeft: "1.2rem" }}>
              {perfil.metodos_mfa.map((m) => (
                <li key={m.tipo} style={{ marginBottom: "0.5rem" }}>
                  <strong>{m.tipo === "app" ? "App autenticadora" : "Código por correo"}</strong>:{" "}
                  {m.activo ? "Activo" : "Pendiente"}{" "}
                  {m.preferido && <span className="badge">Preferido</span>}
                  {m.activo && !m.preferido && (
                    <button
                      type="button"
                      className="btn btn-secondary"
                      style={{ marginLeft: "0.5rem", padding: "0.2rem 0.6rem", fontSize: "0.8rem" }}
                      onClick={() => handleCambiarPreferido(m.tipo)}
                    >
                      Usar por defecto
                    </button>
                  )}
                </li>
              ))}
            </ul>
          )}

          <p style={{ color: "var(--text-secondary)", fontSize: "0.92rem" }}>
            Códigos de respaldo disponibles:{" "}
            <strong>{perfil?.codigos_respaldo_disponibles ?? 0}</strong>
          </p>
          <button type="button" className="btn btn-secondary" onClick={handleGenerarRespaldo}>
            Generar nuevos códigos de respaldo
          </button>

          {codigosRespaldo && (
            <div className="alert alert-warning" style={{ marginTop: "1rem" }}>
              <strong>Guarda estos códigos en un lugar seguro (solo se muestran una vez):</strong>
              <div
                style={{
                  display: "grid",
                  gridTemplateColumns: "repeat(2, 1fr)",
                  gap: "0.35rem",
                  marginTop: "0.5rem",
                  fontFamily: "monospace"
                }}
              >
                {codigosRespaldo.map((c) => (
                  <span key={c}>{c}</span>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
