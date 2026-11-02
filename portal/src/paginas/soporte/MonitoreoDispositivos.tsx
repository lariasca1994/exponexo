import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { ApiClientError } from "../../api/clienteIdentidad";
import { type DeviceItem, helpDeskApi } from "../../api/clienteMesaAyuda";

export function MonitoreoDispositivos() {
  const [devices, setDevices] = useState<DeviceItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [scanning, setScanning] = useState(false);
  const [feedback, setFeedback] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function loadDevices() {
    setLoading(true);
    setError(null);
    try {
      const data = await helpDeskApi.listDevices();
      setDevices(data);
    } catch (err) {
      setError(
        err instanceof ApiClientError
          ? err.message
          : "Error al cargar la lista de dispositivos del recinto."
      );
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void loadDevices();
  }, []);

  async function handleTriggerScan() {
    setScanning(true);
    setError(null);
    setFeedback(null);
    try {
      const res = await helpDeskApi.triggerScanCycle();
      setFeedback(
        `Barrido completado: ${res.dispositivos_caidos_detectados} dispositivos caídos detectados, ${res.sla_vencidos_detectados} vencimientos SLA notificados.`
      );
      await loadDevices();
    } catch (err) {
      setError(err instanceof ApiClientError ? err.message : "Error al ejecutar el barrido de monitoreo.");
    } finally {
      setScanning(false);
    }
  }

  return (
    <main className="container" style={{ paddingBlock: "2rem" }}>
      <header
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          marginBottom: "1.5rem",
          flexWrap: "wrap",
          gap: "1rem"
        }}
      >
        <div>
          <span className="badge">Operaciones del Recinto · Detección de Caídas</span>
          <h1 style={{ margin: "0.25rem 0 0 0" }}>Monitoreo de Kioscos y Pantallas</h1>
        </div>
        <div style={{ display: "flex", gap: "0.75rem" }}>
          <button
            type="button"
            className="btn btn-primary"
            onClick={() => void handleTriggerScan()}
            disabled={scanning}
          >
            {scanning ? "Escaneando recinto..." : "Ejecutar barrido de caídas"}
          </button>
          <Link to="/soporte/tickets" className="btn btn-secondary">
            Mesa de ayuda
          </Link>
          <Link to="/inicio" className="btn btn-secondary">
            Volver
          </Link>
        </div>
      </header>

      {error && <div role="alert" className="alert alert-error">{error}</div>}
      {feedback && <div role="status" className="alert alert-success">{feedback}</div>}

      <section className="panel-card">
        <h2 style={{ marginTop: 0, fontSize: "1.2rem" }}>Dispositivos desplegados en el recinto</h2>
        {loading ? (
          <p>Consultando estado de dispositivos...</p>
        ) : devices.length === 0 ? (
          <p style={{ color: "var(--text-secondary)" }}>
            No hay dispositivos registrados aún. Los kioscos y pantallas se enrolan automáticamente
            con su código secreto de recinto.
          </p>
        ) : (
          <div
            style={{
              display: "grid",
              gridTemplateColumns: "repeat(auto-fit, minmax(280px, 1fr))",
              gap: "1rem",
              marginTop: "1rem"
            }}
          >
            {devices.map((d) => (
              <div
                key={d.id}
                style={{
                  padding: "1.2rem",
                  borderRadius: "var(--radius-md)",
                  border: "1px solid var(--border-color)",
                  background: "var(--bg-page)",
                  display: "flex",
                  flexDirection: "column",
                  gap: "0.5rem"
                }}
              >
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                  <strong style={{ fontSize: "1.05rem" }}>{d.codigo}</strong>
                  <span
                    className="badge"
                    style={{
                      background:
                        d.estado === "en_linea"
                          ? "var(--feedback-success-bg)"
                          : "var(--feedback-error-bg)",
                      color:
                        d.estado === "en_linea"
                          ? "var(--feedback-success-text)"
                          : "var(--feedback-error-text)"
                    }}
                  >
                    {d.estado.toUpperCase().replace("_", " ")}
                  </span>
                </div>

                <p style={{ margin: "0.2rem 0", fontSize: "0.9rem" }}>
                  📍 {d.ubicacion} · Tipo: <strong>{d.tipo.toUpperCase()}</strong>
                </p>

                <div style={{ fontSize: "0.82rem", color: "var(--text-secondary)" }}>
                  <p style={{ margin: "0.2rem 0" }}>Firmware: v{d.version_firmware}</p>
                  <p style={{ margin: "0.2rem 0" }}>
                    Último reporte: {new Date(d.ultimo_reporte_en).toLocaleString("es-CO")}
                  </p>
                  {d.ticket_abierto_id && (
                    <p style={{ margin: "0.2rem 0", color: "var(--feedback-error-text)", fontWeight: 600 }}>
                      Ticket automático activo: {d.ticket_abierto_id.slice(0, 8)}
                    </p>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </section>
    </main>
  );
}
