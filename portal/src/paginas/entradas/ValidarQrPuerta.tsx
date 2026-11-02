import { type FormEvent, useState } from "react";
import { Link } from "react-router-dom";
import { ApiClientError, identityApi } from "../../api/clienteIdentidad";
import type { ValidateTicketQrResult } from "../../tipos/identidad";

export function ValidarQrPuerta() {
  const [qrInput, setQrInput] = useState("");
  const [deviceId, setDeviceId] = useState("torniquete-principal-01");
  const [submitting, setSubmitting] = useState(false);
  const [result, setResult] = useState<ValidateTicketQrResult | null>(null);
  const [error, setError] = useState<{ status: number; message: string } | null>(null);

  async function handleValidate(e: FormEvent) {
    e.preventDefault();
    setSubmitting(true);
    setResult(null);
    setError(null);
    try {
      const res = await identityApi.validateTicketQr(qrInput.trim(), deviceId.trim());
      setResult(res);
    } catch (err) {
      if (err instanceof ApiClientError) {
        setError({ status: err.status, message: err.message });
      } else {
        setError({ status: 500, message: "No fue posible validar el código QR." });
      }
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <main className="contenedor" style={{ paddingBlock: "2rem", maxWidth: "680px" }}>
      <header
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          marginBottom: "1.5rem"
        }}
      >
        <div>
          <p className="etiqueta">Control de acceso · Personal del recinto</p>
          <h1 style={{ margin: "0.25rem 0 0 0" }}>Validar QR en puerta</h1>
        </div>
        <Link to="/inicio" className="boton boton-secundario">
          Volver
        </Link>
      </header>

      <section className="tarjeta">
        <form onSubmit={handleValidate} style={{ display: "grid", gap: "1rem" }}>
          <label className="campo">
            <span>Identificador del punto o torniquete</span>
            <input
              type="text"
              value={deviceId}
              onChange={(e) => setDeviceId(e.target.value)}
              required
            />
          </label>

          <label className="campo">
            <span>Cadena del código QR escaneado (`EXN1...`)</span>
            <textarea
              rows={3}
              value={qrInput}
              onChange={(e) => setQrInput(e.target.value)}
              placeholder="Pega o escanea aquí el contenido firmado EXN1..."
              required
            />
          </label>

          <button type="submit" className="boton boton-primario" disabled={submitting}>
            {submitting ? "Verificando firma..." : "Validar e ingresar"}
          </button>
        </form>

        {result && (
          <div
            role="status"
            style={{
              marginTop: "1.25rem",
              padding: "1rem",
              borderRadius: "8px",
              border: "1px solid var(--color-exito)",
              background: "rgba(22, 163, 74, 0.08)"
            }}
          >
            <strong style={{ color: "var(--color-exito)" }}>
              INGRESO AUTORIZADO · Firma auténtica
            </strong>
            <p className="numero-tabular" style={{ margin: "0.5rem 0 0 0", fontSize: "0.9rem" }}>
              Entrada: {result.entrada_id} · Categoría: {result.tipo.toUpperCase()} ·
              Dispositivo: {result.usada_en_dispositivo}
            </p>
          </div>
        )}

        {error && (
          <div
            role="alert"
            className="alerta alerta-error"
            style={{ marginTop: "1.25rem" }}
          >
            <strong>
              {error.status === 409
                ? "ACCESO RECHAZADO (409 · Entrada ya utilizada)"
                : error.status === 400
                ? "QR INVÁLIDO (400 · Firma criptográfica alterada)"
                : `Error (${error.status})`}
            </strong>
            <p style={{ margin: "0.35rem 0 0 0" }}>{error.message}</p>
          </div>
        )}
      </section>
    </main>
  );
}
