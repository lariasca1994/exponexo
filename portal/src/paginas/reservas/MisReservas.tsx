import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { identityApi } from "../../api/clienteIdentidad";
import type { StandReservationItem } from "../../tipos/identidad";

export function MisReservas() {
  const [reservas, setReservas] = useState<StandReservationItem[]>([]);
  const [cargando, setCargando] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [mensaje, setMensaje] = useState<string | null>(null);

  const cargar = async () => {
    setCargando(true);
    try {
      const data = await identityApi.listMyReservations();
      setReservas(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "No se pudieron cargar tus reservas.");
    } finally {
      setCargando(false);
    }
  };

  useEffect(() => {
    void cargar();
  }, []);

  const handleCancelar = async (id: string) => {
    setError(null);
    setMensaje(null);
    try {
      await identityApi.cancelReservation(id);
      setMensaje("Reserva cancelada y stand liberado.");
      await cargar();
    } catch (err) {
      setError(err instanceof Error ? err.message : "No se pudo cancelar la reserva.");
    }
  };

  return (
    <div className="container">
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          marginBottom: "1rem",
          flexWrap: "wrap",
          gap: "0.75rem"
        }}
      >
        <h1 style={{ margin: 0 }}>Mis Reservas de Stands</h1>
        <Link to="/eventos" className="btn btn-primary">
          Explorar eventos y stands
        </Link>
      </div>

      {error && <div className="alert alert-error">{error}</div>}
      {mensaje && <div className="alert alert-success">{mensaje}</div>}
      {cargando && <div className="panel-card">Cargando tus reservas…</div>}

      {!cargando && reservas.length === 0 && (
        <div className="panel-card">
          No tienes reservas registradas. Ve a <Link to="/eventos">Eventos</Link> para elegir un
          stand en el plano.
        </div>
      )}

      <div className="grid-2">
        {reservas.map((r) => (
          <div key={r.id} className="panel-card">
            <span className="badge">{r.estado.toUpperCase()}</span>
            <h3 style={{ marginBottom: "0.4rem" }}>Reserva #{r.id.slice(0, 8)}</h3>
            <p style={{ margin: "0.3rem 0" }}>
              <strong>Monto congelado:</strong> ${Number(r.monto).toLocaleString()} COP
            </p>
            <p style={{ margin: "0.3rem 0", fontSize: "0.88rem", color: "var(--text-secondary)" }}>
              <strong>Vence en:</strong> {new Date(r.vence_en).toLocaleString()}
            </p>
            {r.estado === "pendiente_pago" && (
              <div style={{ display: "flex", gap: "0.75rem", marginTop: "1rem", flexWrap: "wrap" }}>
                <Link to={`/pagar/stand/${r.id}`} className="btn btn-primary">
                  Pagar con QR
                </Link>
                <button
                  type="button"
                  className="btn btn-secondary"
                  onClick={() => handleCancelar(r.id)}
                >
                  Cancelar reserva
                </button>
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
