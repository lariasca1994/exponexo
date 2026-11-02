import { type FormEvent, useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { ApiClientError, identityApi } from "../../api/clienteIdentidad";
import { useSession } from "../../sesion/almacenSesion";
import type { AppointmentItem, EventItem, FreeSlotItem } from "../../tipos/identidad";

export function AgendaNegocios() {
  const { user } = useSession();
  const [events, setEvents] = useState<EventItem[]>([]);
  const [selectedEventId, setSelectedEventId] = useState("");
  const [exhibitors, setExhibitors] = useState<
    { id: string; nombre_completo: string; empresa_nombre: string | null }[]
  >([]);
  const [selectedExhibitorId, setSelectedExhibitorId] = useState("");
  const [freeSlots, setFreeSlots] = useState<FreeSlotItem[]>([]);
  const [appointments, setAppointments] = useState<AppointmentItem[]>([]);

  const [blockStart, setBlockStart] = useState("2026-11-15T14:00");
  const [blockEnd, setBlockEnd] = useState("2026-11-15T17:00");

  const [propStart, setPropStart] = useState("2026-11-15T14:00");
  const [propEnd, setPropEnd] = useState("2026-11-15T14:45");
  const [propMessage, setPropMessage] = useState("");

  const [feedback, setFeedback] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function loadBase() {
    try {
      const [evPage, myAppts] = await Promise.all([
        identityApi.listEvents(1, 20),
        identityApi.listMyAppointments()
      ]);
      setEvents(evPage.items);
      setAppointments(myAppts);
      if (evPage.items.length > 0 && !selectedEventId) {
        setSelectedEventId(evPage.items[0].id);
      }
    } catch (err) {
      setError(
        err instanceof ApiClientError
          ? err.message
          : "No fue posible cargar la agenda de negocios."
      );
    }
  }

  useEffect(() => {
    void loadBase();
  }, []);

  useEffect(() => {
    if (!selectedEventId) return;
    identityApi
      .listEventExhibitors(selectedEventId)
      .then((list) => {
        setExhibitors(list);
        if (list.length > 0) {
          setSelectedExhibitorId(list[0].id);
        }
      })
      .catch(() => setExhibitors([]));
  }, [selectedEventId]);

  useEffect(() => {
    if (!selectedEventId || !selectedExhibitorId) {
      setFreeSlots([]);
      return;
    }
    identityApi
      .getExhibitorFreeSlots(selectedEventId, selectedExhibitorId)
      .then(setFreeSlots)
      .catch(() => setFreeSlots([]));
  }, [selectedEventId, selectedExhibitorId, appointments]);

  async function handleSaveAvailability(e: FormEvent) {
    e.preventDefault();
    if (!selectedEventId) return;
    setError(null);
    setFeedback(null);
    try {
      await identityApi.updateMyAvailability(selectedEventId, [
        {
          desde: new Date(blockStart).toISOString(),
          hasta: new Date(blockEnd).toISOString()
        }
      ]);
      setFeedback("Tu disponibilidad fue actualizada para este evento.");
      await loadBase();
    } catch (err) {
      setError(
        err instanceof ApiClientError
          ? err.message
          : "No fue posible guardar tu disponibilidad."
      );
    }
  }

  async function handlePropose(e: FormEvent) {
    e.preventDefault();
    if (!selectedEventId || !selectedExhibitorId) return;
    setError(null);
    setFeedback(null);
    try {
      await identityApi.proposeAppointment({
        evento_id: selectedEventId,
        anfitrion_id: selectedExhibitorId,
        inicio: new Date(propStart).toISOString(),
        fin: new Date(propEnd).toISOString(),
        mensaje: propMessage || undefined
      });
      setFeedback("Propuesta de cita enviada correctamente.");
      setPropMessage("");
      await loadBase();
    } catch (err) {
      setError(
        err instanceof ApiClientError
          ? err.message
          : "No fue posible proponer la cita."
      );
    }
  }

  async function handleRespond(id: string, decision: "aceptar" | "rechazar") {
    setError(null);
    setFeedback(null);
    try {
      const updated = await identityApi.respondAppointment(id, decision);
      setFeedback(
        decision === "aceptar"
          ? `Cita aceptada en sala ${updated.sala_codigo || "asignada"}.`
          : "Cita rechazada."
      );
      await loadBase();
    } catch (err) {
      setError(
        err instanceof ApiClientError
          ? err.message
          : "No fue posible responder la cita."
      );
    }
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
          <p className="etiqueta">Rueda de negocios · Asignación automática de sala</p>
          <h1 style={{ margin: "0.25rem 0 0 0" }}>Agenda y citas B2B</h1>
        </div>
        <Link to="/inicio" className="boton boton-secundario">
          Volver al inicio
        </Link>
      </header>

      {error && (
        <div role="alert" className="alerta alerta-error" style={{ marginBottom: "1rem" }}>
          {error}
        </div>
      )}
      {feedback && (
        <div role="status" className="alerta" style={{ marginBottom: "1rem" }}>
          {feedback}
        </div>
      )}

      <div
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(auto-fit, minmax(320px, 1fr))",
          gap: "1.25rem",
          marginBottom: "1.75rem"
        }}
      >
        <section className="tarjeta">
          <h2 style={{ marginTop: 0, fontSize: "1.1rem" }}>
            1. Definir mi disponibilidad en el evento
          </h2>
          <form onSubmit={handleSaveAvailability} style={{ display: "grid", gap: "0.85rem" }}>
            <label className="campo">
              <span>Evento</span>
              <select
                value={selectedEventId}
                onChange={(e) => setSelectedEventId(e.target.value)}
              >
                {events.map((ev) => (
                  <option key={ev.id} value={ev.id}>
                    {ev.nombre}
                  </option>
                ))}
              </select>
            </label>

            <label className="campo">
              <span>Disponible desde</span>
              <input
                type="datetime-local"
                value={blockStart}
                onChange={(e) => setBlockStart(e.target.value)}
                required
              />
            </label>

            <label className="campo">
              <span>Disponible hasta</span>
              <input
                type="datetime-local"
                value={blockEnd}
                onChange={(e) => setBlockEnd(e.target.value)}
                required
              />
            </label>

            <button type="submit" className="boton boton-secundario">
              Guardar bloque libre
            </button>
          </form>
        </section>

        <section className="tarjeta">
          <h2 style={{ marginTop: 0, fontSize: "1.1rem" }}>
            2. Consultar huecos y proponer cita
          </h2>
          <form onSubmit={handlePropose} style={{ display: "grid", gap: "0.85rem" }}>
            <label className="campo">
              <span>Expositor anfitrión</span>
              <select
                value={selectedExhibitorId}
                onChange={(e) => setSelectedExhibitorId(e.target.value)}
              >
                {exhibitors.map((ex) => (
                  <option key={ex.id} value={ex.id}>
                    {ex.nombre_completo}
                  </option>
                ))}
              </select>
            </label>

            {freeSlots.length > 0 && (
              <div style={{ fontSize: "0.82rem", color: "var(--color-texto-suave)" }}>
                <strong>Huecos libres del expositor:</strong>
                <ul style={{ margin: "0.25rem 0 0 1.1rem", padding: 0 }}>
                  {freeSlots.map((slot, idx) => (
                    <li key={idx} className="numero-tabular">
                      {new Date(slot.desde).toLocaleString("es-CO")} →{" "}
                      {new Date(slot.hasta).toLocaleTimeString("es-CO")}
                    </li>
                  ))}
                </ul>
              </div>
            )}

            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "0.75rem" }}>
              <label className="campo">
                <span>Inicio</span>
                <input
                  type="datetime-local"
                  value={propStart}
                  onChange={(e) => setPropStart(e.target.value)}
                  required
                />
              </label>
              <label className="campo">
                <span>Fin</span>
                <input
                  type="datetime-local"
                  value={propEnd}
                  onChange={(e) => setPropEnd(e.target.value)}
                  required
                />
              </label>
            </div>

            <label className="campo">
              <span>Mensaje o motivo comercial</span>
              <input
                type="text"
                value={propMessage}
                onChange={(e) => setPropMessage(e.target.value)}
                placeholder="Ej. Distribución regional de maquinaria"
              />
            </label>

            <button type="submit" className="boton boton-primario">
              Proponer cita
            </button>
          </form>
        </section>
      </div>

      <section className="tarjeta">
        <h2 style={{ marginTop: 0, fontSize: "1.15rem" }}>Mis citas programadas y propuestas</h2>
        {appointments.length === 0 ? (
          <p style={{ margin: 0 }}>No tienes citas registradas todavía.</p>
        ) : (
          <div style={{ display: "grid", gap: "0.75rem" }}>
            {appointments.map((appt) => {
              const isHost = user?.id === appt.anfitrion_id;
              return (
                <div
                  key={appt.id}
                  style={{
                    padding: "1rem",
                    borderRadius: "8px",
                    border: "1px solid var(--color-borde)",
                    display: "flex",
                    justifyContent: "space-between",
                    alignItems: "center",
                    flexWrap: "wrap",
                    gap: "1rem"
                  }}
                >
                  <div>
                    <span className="etiqueta">{appt.estado.toUpperCase()}</span>
                    <p style={{ margin: "0.35rem 0", fontWeight: 600 }}>
                      Solicita: {appt.solicitante_nombre || appt.solicitante_id.slice(0, 8)} ·
                      Anfitrión: {appt.anfitrion_nombre || appt.anfitrion_id.slice(0, 8)}
                    </p>
                    <p className="numero-tabular" style={{ margin: 0, fontSize: "0.88rem" }}>
                      Horario: {new Date(appt.inicio).toLocaleString("es-CO")} –{" "}
                      {new Date(appt.fin).toLocaleTimeString("es-CO")}
                      {appt.sala_codigo && ` · Sala asignada: ${appt.sala_codigo}`}
                    </p>
                    {appt.mensaje && (
                      <p style={{ margin: "0.25rem 0 0 0", fontSize: "0.85rem" }}>
                        «{appt.mensaje}»
                      </p>
                    )}
                  </div>

                  {appt.estado === "propuesta" && isHost && (
                    <div style={{ display: "flex", gap: "0.5rem" }}>
                      <button
                        type="button"
                        className="boton boton-primario"
                        onClick={() => void handleRespond(appt.id, "aceptar")}
                      >
                        Aceptar y asignar sala
                      </button>
                      <button
                        type="button"
                        className="boton boton-secundario"
                        onClick={() => void handleRespond(appt.id, "rechazar")}
                      >
                        Rechazar
                      </button>
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        )}
      </section>
    </main>
  );
}
