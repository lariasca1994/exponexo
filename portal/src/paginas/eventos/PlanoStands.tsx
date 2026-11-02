import { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { identityApi } from "../../api/clienteIdentidad";
import { useSession } from "../../sesion/almacenSesion";
import type { EventItem, StandStatusItem } from "../../tipos/identidad";

const STATUS_COLORS: Record<StandStatusItem["estado"], string> = {
  disponible: "var(--status-available)",
  reservado: "var(--status-reserved)",
  pagado: "var(--status-paid)"
};

export function PlanoStands() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { user } = useSession();

  const [evento, setEvento] = useState<EventItem | null>(null);
  const [stands, setStands] = useState<StandStatusItem[]>([]);
  const [seleccionado, setSeleccionado] = useState<StandStatusItem | null>(null);
  const [mensaje, setMensaje] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [cargando, setCargando] = useState(true);
  const [reservando, setReservando] = useState(false);

  const cargarPlano = async () => {
    if (!id) return;
    setCargando(true);
    try {
      const [evData, stData] = await Promise.all([
        identityApi.getEvent(id),
        identityApi.getEventStands(id)
      ]);
      setEvento(evData);
      setStands(stData);
    } catch (err) {
      setError(err instanceof Error ? err.message : "No se pudo cargar el plano del evento.");
    } finally {
      setCargando(false);
    }
  };

  useEffect(() => {
    void cargarPlano();
  }, [id]);

  const handleReservar = async () => {
    if (!evento || !seleccionado) return;
    setError(null);
    setMensaje(null);
    setReservando(true);
    try {
      await identityApi.reserveStand({
        evento_id: evento.id,
        stand_id: seleccionado.id
      });
      setMensaje(`Stand ${seleccionado.codigo} reservado con éxito (pendiente de pago).`);
      await cargarPlano();
      setTimeout(() => navigate("/reservas"), 1200);
    } catch (err) {
      setError(err instanceof Error ? err.message : "No se pudo reservar el stand.");
    } finally {
      setReservando(false);
    }
  };

  return (
    <div className="container">
      <h1 style={{ marginTop: 0 }}>
        Plano de Stands {evento ? `· ${evento.nombre}` : ""}
      </h1>

      <div style={{ display: "flex", gap: "1rem", marginBottom: "1.25rem", flexWrap: "wrap" }}>
        <span className="badge" style={{ borderLeft: "4px solid var(--status-available)" }}>
          Disponible
        </span>
        <span className="badge" style={{ borderLeft: "4px solid var(--status-reserved)" }}>
          Reservado (pendiente de pago)
        </span>
        <span className="badge" style={{ borderLeft: "4px solid var(--status-paid)" }}>
          Pagado
        </span>
      </div>

      {error && <div className="alert alert-error">{error}</div>}
      {mensaje && <div className="alert alert-success">{mensaje}</div>}
      {cargando && <div className="panel-card">Cargando cuadrícula de stands…</div>}

      <div className="grid-2">
        <div className="panel-card">
          <h3 style={{ marginTop: 0 }}>Cuadrícula de stands</h3>
          {stands.length === 0 ? (
            <p style={{ color: "var(--text-secondary)" }}>
              No hay stands registrados para este evento todavía.
            </p>
          ) : (
            <div
              style={{
                display: "grid",
                gridTemplateColumns: "repeat(auto-fill, minmax(110px, 1fr))",
                gap: "0.75rem"
              }}
            >
              {stands.map((st) => (
                <button
                  key={st.id}
                  type="button"
                  onClick={() => setSeleccionado(st)}
                  style={{
                    padding: "0.75rem 0.5rem",
                    borderRadius: "var(--radius-md)",
                    border:
                      seleccionado?.id === st.id
                        ? "2px solid var(--text-primary)"
                        : "1px solid var(--border-color)",
                    background: STATUS_COLORS[st.estado],
                    color: "#ffffff",
                    fontWeight: 700,
                    cursor: "pointer",
                    textAlign: "center"
                  }}
                >
                  <div>{st.codigo}</div>
                  <div style={{ fontSize: "0.75rem", fontWeight: 500 }}>
                    {st.metros_cuadrados} m²
                  </div>
                </button>
              ))}
            </div>
          )}
        </div>

        <div className="panel-card">
          <h3 style={{ marginTop: 0 }}>Detalle del stand</h3>
          {!seleccionado ? (
            <p style={{ color: "var(--text-secondary)" }}>
              Haz clic en un stand de la cuadrícula para ver sus dimensiones, ubicación, precio y
              disponibilidad.
            </p>
          ) : (
            <div>
              <p>
                <strong>Código:</strong> {seleccionado.codigo} ({seleccionado.pabellon_nombre})
              </p>
              <p>
                <strong>Tipo:</strong> {seleccionado.tipo} · <strong>Área:</strong>{" "}
                {seleccionado.metros_cuadrados} m²
              </p>
              <p>
                <strong>Posición:</strong> Fila {seleccionado.fila}, Columna {seleccionado.columna}
              </p>
              <p>
                <strong>Precio base:</strong> ${Number(seleccionado.precio_base).toLocaleString()} COP
              </p>
              <p>
                <strong>Estado actual:</strong>{" "}
                <span className="badge">{seleccionado.estado.toUpperCase()}</span>
              </p>

              {seleccionado.estado === "disponible" && user?.rol === "expositor" && (
                <button
                  type="button"
                  className="btn btn-primary"
                  style={{ width: "100%", marginTop: "0.75rem" }}
                  disabled={reservando}
                  onClick={handleReservar}
                >
                  {reservando ? "Reservando stand…" : "Reservar este stand"}
                </button>
              )}

              {seleccionado.estado === "disponible" && user?.rol !== "expositor" && (
                <p style={{ fontSize: "0.88rem", color: "var(--text-secondary)" }}>
                  Ingresa con una cuenta de rol <strong>Expositor</strong> para reservar este stand.
                </p>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
