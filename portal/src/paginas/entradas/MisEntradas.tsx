import { type FormEvent, useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { ApiClientError, identityApi } from "../../api/clienteIdentidad";
import type { EventItem, TicketItem } from "../../tipos/identidad";

export function MisEntradas() {
  const navigate = useNavigate();
  const [tickets, setTickets] = useState<TicketItem[]>([]);
  const [events, setEvents] = useState<EventItem[]>([]);
  const [selectedEventId, setSelectedEventId] = useState("");
  const [selectedType, setSelectedType] = useState<"general" | "negocios" | "prensa">(
    "general"
  );
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function loadData() {
    setLoading(true);
    setError(null);
    try {
      const [myTickets, evPage] = await Promise.all([
        identityApi.listMyTickets(),
        identityApi.listEvents(1, 30)
      ]);
      setTickets(myTickets);
      setEvents(evPage.items);
      if (evPage.items.length > 0 && !selectedEventId) {
        setSelectedEventId(evPage.items[0].id);
      }
    } catch (err) {
      setError(
        err instanceof ApiClientError
          ? err.message
          : "No fue posible cargar tus entradas."
      );
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void loadData();
  }, []);

  async function handleBuyTicket(e: FormEvent) {
    e.preventDefault();
    if (!selectedEventId) return;
    setSubmitting(true);
    setError(null);
    try {
      await identityApi.purchaseTicket(selectedEventId, selectedType);
      await loadData();
    } catch (err) {
      setError(
        err instanceof ApiClientError
          ? err.message
          : "No fue posible registrar la compra de la entrada."
      );
    } finally {
      setSubmitting(false);
    }
  }

  function handleGoToPay(ticket: TicketItem) {
    navigate(`/pagar/entrada/${ticket.id}`);
  }

  return (
    <main className="contenedor" style={{ paddingBlock: "2rem" }}>
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
          <p className="etiqueta">Acceso al recinto · Código QR firmado</p>
          <h1 style={{ margin: "0.25rem 0 0 0" }}>Mis entradas</h1>
        </div>
        <Link to="/inicio" className="boton boton-secundario">
          Volver al inicio
        </Link>
      </header>

      {error && (
        <div role="alert" className="alerta alerta-error" style={{ marginBottom: "1.25rem" }}>
          {error}
        </div>
      )}

      <section className="tarjeta" style={{ marginBottom: "1.75rem" }}>
        <h2 style={{ marginTop: 0, fontSize: "1.15rem" }}>Adquirir nueva entrada</h2>
        <form
          onSubmit={handleBuyTicket}
          style={{
            display: "grid",
            gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))",
            gap: "1rem",
            alignItems: "end"
          }}
        >
          <label className="campo">
            <span>Evento</span>
            <select
              value={selectedEventId}
              onChange={(e) => setSelectedEventId(e.target.value)}
              required
            >
              {events.map((ev) => (
                <option key={ev.id} value={ev.id}>
                  {ev.nombre}
                </option>
              ))}
            </select>
          </label>

          <label className="campo">
            <span>Categoría de entrada</span>
            <select
              value={selectedType}
              onChange={(e) =>
                setSelectedType(e.target.value as "general" | "negocios" | "prensa")
              }
            >
              <option value="general">General ($45.000 COP)</option>
              <option value="negocios">Rueda de Negocios ($120.000 COP)</option>
              <option value="prensa">Prensa acreditada ($25.000 COP)</option>
            </select>
          </label>

          <button
            type="submit"
            className="boton boton-primario"
            disabled={submitting || events.length === 0}
          >
            {submitting ? "Solicitando..." : "Solicitar entrada"}
          </button>
        </form>
      </section>

      {loading ? (
        <p>Cargando tus entradas...</p>
      ) : tickets.length === 0 ? (
        <div className="tarjeta">
          <p style={{ margin: 0 }}>
            Aún no tienes entradas registradas. Solicita una arriba para obtener tu QR de acceso.
          </p>
        </div>
      ) : (
        <div
          style={{
            display: "grid",
            gridTemplateColumns: "repeat(auto-fit, minmax(310px, 1fr))",
            gap: "1rem"
          }}
        >
          {tickets.map((t) => (
            <article key={t.id} className="tarjeta">
              <div
                style={{
                  display: "flex",
                  justifyContent: "space-between",
                  alignItems: "center",
                  marginBottom: "0.75rem"
                }}
              >
                <span className="etiqueta">{t.tipo.toUpperCase()}</span>
                <span
                  style={{
                    fontSize: "0.8rem",
                    fontWeight: 600,
                    color:
                      t.estado === "activa"
                        ? "var(--color-exito)"
                        : t.estado === "usada"
                        ? "var(--color-texto-suave)"
                        : "var(--color-advertencia)"
                  }}
                >
                  {t.estado.replace("_", " ").toUpperCase()}
                </span>
              </div>

              <h3 style={{ margin: "0 0 0.5rem 0" }}>
                {t.evento_nombre || `Evento ${t.evento_id.slice(0, 8)}`}
              </h3>
              <p className="numero-tabular" style={{ margin: "0 0 0.75rem 0", fontSize: "0.9rem" }}>
                Valor: ${Number(t.precio_sugerido).toLocaleString("es-CO")} COP
              </p>

              {t.estado === "pendiente_pago" && (
                <button
                  type="button"
                  className="boton boton-primario"
                  onClick={() => void handleGoToPay(t)}
                >
                  Pagar y activar QR
                </button>
              )}

              {t.codigo_qr && (
                <div
                  style={{
                    marginTop: "0.75rem",
                    padding: "0.75rem",
                    borderRadius: "8px",
                    background: "var(--color-superficie-2)",
                    border: "1px dashed var(--color-borde)"
                  }}
                >
                  <p style={{ margin: "0 0 0.35rem 0", fontSize: "0.78rem", fontWeight: 600 }}>
                    Código QR firmado (disponible sin conexión):
                  </p>
                  <code
                    style={{
                      display: "block",
                      wordBreak: "break-all",
                      fontSize: "0.75rem"
                    }}
                  >
                    {t.codigo_qr}
                  </code>
                </div>
              )}

              {t.usada_en && (
                <p style={{ margin: "0.75rem 0 0 0", fontSize: "0.8rem", color: "var(--color-texto-suave)" }}>
                  Validada en puerta ({t.usada_en_dispositivo}) el{" "}
                  {new Date(t.usada_en).toLocaleString("es-CO")}
                </p>
              )}
            </article>
          ))}
        </div>
      )}
    </main>
  );
}
