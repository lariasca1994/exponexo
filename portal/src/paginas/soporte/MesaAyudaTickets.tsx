import { type FormEvent, useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { ApiClientError } from "../../api/clienteIdentidad";
import { helpDeskApi, type TicketItem } from "../../api/clienteMesaAyuda";
import { useSession } from "../../sesion/almacenSesion";

export function MesaAyudaTickets() {
  const { user } = useSession();
  const [tickets, setTickets] = useState<TicketItem[]>([]);
  const [filterState, setFilterState] = useState("");
  const [filterPriority, setFilterPriority] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [feedback, setFeedback] = useState<string | null>(null);

  // Form state
  const [ubicacion, setUbicacion] = useState("");
  const [categoria, setCategoria] = useState("red");
  const [prioridad, setPrioridad] = useState<"baja" | "media" | "alta" | "critica">("media");
  const [descripcion, setDescripcion] = useState("");
  const [submitting, setSubmitting] = useState(false);

  // Resolve modal state
  const [resolvingId, setResolvingId] = useState<string | null>(null);
  const [resolveNote, setResolveNote] = useState("");

  const isStaff = user?.rol === "personal" || user?.rol === "administrador";

  async function loadTickets() {
    setLoading(true);
    setError(null);
    try {
      const data = await helpDeskApi.listTickets({
        estado: filterState || undefined,
        prioridad: filterPriority || undefined
      });
      setTickets(data);
    } catch (err) {
      setError(
        err instanceof ApiClientError
          ? err.message
          : "No se pudieron cargar los tickets de soporte."
      );
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void loadTickets();
  }, [filterState, filterPriority]);

  async function handleCreateTicket(e: FormEvent) {
    e.preventDefault();
    setSubmitting(true);
    setError(null);
    setFeedback(null);
    try {
      const created = await helpDeskApi.createTicket({
        ubicacion,
        categoria,
        prioridad,
        descripcion
      });
      setFeedback(`Ticket ${created.numero} abierto exitosamente con prioridad ${created.prioridad.toUpperCase()}.`);
      setUbicacion("");
      setDescripcion("");
      await loadTickets();
    } catch (err) {
      setError(err instanceof ApiClientError ? err.message : "Error al abrir el ticket.");
    } finally {
      setSubmitting(false);
    }
  }

  async function handleTake(id: string) {
    setError(null);
    try {
      await helpDeskApi.takeTicket(id);
      setFeedback("Ticket tomado para atención (en_atencion).");
      await loadTickets();
    } catch (err) {
      setError(err instanceof ApiClientError ? err.message : "Error al tomar el ticket.");
    }
  }

  async function handleEscalate(id: string) {
    setError(null);
    try {
      const updated = await helpDeskApi.escalateTicket(id, "Escalamiento solicitado por el personal");
      setFeedback(`Ticket escalado a nivel ${updated.nivel_actual}.`);
      await loadTickets();
    } catch (err) {
      setError(err instanceof ApiClientError ? err.message : "No fue posible escalar el ticket.");
    }
  }

  async function handleResolveSubmit(e: FormEvent) {
    e.preventDefault();
    if (!resolvingId || !resolveNote.trim()) return;
    setError(null);
    try {
      await helpDeskApi.resolveTicket(resolvingId, resolveNote.trim());
      setFeedback("Ticket marcado como resuelto con éxito.");
      setResolvingId(null);
      setResolveNote("");
      await loadTickets();
    } catch (err) {
      setError(err instanceof ApiClientError ? err.message : "Error al resolver el ticket.");
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
          <span className="badge">Mesa de ayuda · SLA & Escalamiento N1/N2/N3</span>
          <h1 style={{ margin: "0.25rem 0 0 0" }}>Soporte técnico del recinto</h1>
        </div>
        <div style={{ display: "flex", gap: "0.75rem" }}>
          {isStaff && (
            <Link to="/soporte/dispositivos" className="btn btn-secondary">
              Monitoreo de kioscos
            </Link>
          )}
          <Link to="/inicio" className="btn btn-secondary">
            Volver
          </Link>
        </div>
      </header>

      {error && <div role="alert" className="alert alert-error">{error}</div>}
      {feedback && <div role="status" className="alert alert-success">{feedback}</div>}

      <div className="grid-2" style={{ marginBottom: "2rem" }}>
        {/* Formulario para abrir ticket */}
        <section className="panel-card">
          <h2 style={{ marginTop: 0, fontSize: "1.2rem" }}>Abrir nuevo ticket de soporte</h2>
          <form onSubmit={handleCreateTicket}>
            <div className="form-group">
              <label>Ubicación exacta (pabellón, stand, puerta)</label>
              <input
                type="text"
                value={ubicacion}
                onChange={(e) => setUbicacion(e.target.value)}
                placeholder="Ej. Pabellón 2 · Stand C-04"
                required
              />
            </div>

            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "1rem" }}>
              <div className="form-group">
                <label>Categoría</label>
                <select value={categoria} onChange={(e) => setCategoria(e.target.value)}>
                  <option value="red">Conectividad / Red Wi-Fi</option>
                  <option value="electrico">Energía / Eléctrico</option>
                  <option value="mobiliario">Mobiliario / Estructura</option>
                  <option value="acceso">Control de acceso / Torniquete</option>
                  <option value="dispositivo">Kiosco / Pantalla</option>
                  <option value="otro">Otro incidente</option>
                </select>
              </div>

              <div className="form-group">
                <label>Prioridad (acuerdo SLA)</label>
                <select
                  value={prioridad}
                  onChange={(e) =>
                    setPrioridad(e.target.value as "baja" | "media" | "alta" | "critica")
                  }
                >
                  <option value="baja">Baja (Resolución 8h)</option>
                  <option value="media">Media (Resolución 4h)</option>
                  <option value="alta">Alta (Resolución 2h)</option>
                  <option value="critica">Crítica (Resolución 1h)</option>
                </select>
              </div>
            </div>

            <div className="form-group">
              <label>Descripción detallada</label>
              <textarea
                rows={3}
                value={descripcion}
                onChange={(e) => setDescripcion(e.target.value)}
                placeholder="Describe el incidente para que el equipo técnico acuda con las herramientas apropiadas."
                required
              />
            </div>

            <button type="submit" className="btn btn-primary" disabled={submitting}>
              {submitting ? "Registrando ticket..." : "Abrir ticket"}
            </button>
          </form>
        </section>

        {/* Políticas de SLA informativas */}
        <section className="panel-card" style={{ display: "flex", flexDirection: "column", justifyContent: "space-between" }}>
          <div>
            <h2 style={{ marginTop: 0, fontSize: "1.2rem" }}>Tiempos de respuesta y SLA</h2>
            <p style={{ color: "var(--text-secondary)", fontSize: "0.9rem" }}>
              Todos los tickets se miden contra el acuerdo de nivel de servicio (SLA). Si el tiempo
              expira sin resolución, el sistema escala automáticamente de Nivel 1 a Nivel 2 y 3 y
              dispara avisos al personal por Telegram.
            </p>
            <ul style={{ paddingLeft: "1.2rem", fontSize: "0.88rem", color: "var(--text-secondary)" }}>
              <li><strong>Crítica:</strong> Respuesta inicial 5 min · Resolución 60 min</li>
              <li><strong>Alta:</strong> Respuesta inicial 15 min · Resolución 120 min</li>
              <li><strong>Media:</strong> Respuesta inicial 30 min · Resolución 240 min</li>
              <li><strong>Baja:</strong> Respuesta inicial 60 min · Resolución 480 min</li>
            </ul>
          </div>
          <div style={{ marginTop: "1rem" }}>
            <span className="badge badge-success">Garantía de servicio 99.8%</span>
          </div>
        </section>
      </div>

      {/* Lista de tickets */}
      <section className="panel-card">
        <div
          style={{
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
            marginBottom: "1.25rem",
            flexWrap: "wrap",
            gap: "1rem"
          }}
        >
          <h2 style={{ margin: 0, fontSize: "1.2rem" }}>Historial y bandeja de tickets</h2>

          <div style={{ display: "flex", gap: "0.75rem", flexWrap: "wrap" }}>
            <select
              value={filterState}
              onChange={(e) => setFilterState(e.target.value)}
              style={{ fontSize: "0.85rem", padding: "0.4rem 0.6rem" }}
            >
              <option value="">Todos los estados</option>
              <option value="abierto">Abiertos</option>
              <option value="en_atencion">En atención</option>
              <option value="escalado">Escalados</option>
              <option value="resuelto">Resueltos</option>
            </select>

            <select
              value={filterPriority}
              onChange={(e) => setFilterPriority(e.target.value)}
              style={{ fontSize: "0.85rem", padding: "0.4rem 0.6rem" }}
            >
              <option value="">Todas las prioridades</option>
              <option value="critica">Crítica</option>
              <option value="alta">Alta</option>
              <option value="media">Media</option>
              <option value="baja">Baja</option>
            </select>
          </div>
        </div>

        {loading ? (
          <p>Cargando tickets...</p>
        ) : tickets.length === 0 ? (
          <p style={{ color: "var(--text-secondary)" }}>No hay tickets con los filtros seleccionados.</p>
        ) : (
          <div style={{ display: "grid", gap: "1rem" }}>
            {tickets.map((t) => {
              const due = new Date(t.sla_vence_en);
              const now = new Date();
              const isOverdue = now > due && t.estado !== "resuelto" && t.estado !== "cerrado";

              return (
                <article
                  key={t.id}
                  style={{
                    padding: "1.2rem",
                    borderRadius: "var(--radius-md)",
                    border: "1px solid var(--border-color)",
                    background: "var(--bg-page)",
                    display: "flex",
                    flexDirection: "column",
                    gap: "0.6rem"
                  }}
                >
                  <div style={{ display: "flex", justifyContent: "space-between", flexWrap: "wrap", gap: "0.5rem" }}>
                    <div style={{ display: "flex", gap: "0.5rem", alignItems: "center" }}>
                      <strong style={{ fontSize: "1.05rem" }}>{t.numero}</strong>
                      <span className="badge">{t.categoria.toUpperCase()}</span>
                      <span
                        className="badge"
                        style={{
                          background:
                            t.prioridad === "critica" || t.prioridad === "alta"
                              ? "var(--feedback-error-bg)"
                              : "var(--bg-subtle)",
                          color:
                            t.prioridad === "critica" || t.prioridad === "alta"
                              ? "var(--feedback-error-text)"
                              : "inherit"
                        }}
                      >
                        {t.prioridad.toUpperCase()}
                      </span>
                      <span className="badge">Nivel: {t.nivel_actual}</span>
                    </div>

                    <div>
                      <span
                        style={{
                          fontWeight: 700,
                          fontSize: "0.85rem",
                          color:
                            t.estado === "resuelto"
                              ? "var(--status-available)"
                              : isOverdue
                              ? "var(--feedback-error-text)"
                              : "var(--brand-primary)"
                        }}
                      >
                        {t.estado.toUpperCase().replace("_", " ")}
                        {isOverdue && " (SLA VENCIDO)"}
                      </span>
                    </div>
                  </div>

                  <p style={{ margin: "0.25rem 0", fontSize: "0.95rem" }}>{t.descripcion}</p>

                  <div style={{ fontSize: "0.83rem", color: "var(--text-secondary)", display: "flex", flexWrap: "wrap", gap: "1rem" }}>
                    <span>📍 Ubicación: <strong>{t.ubicacion}</strong></span>
                    <span>🕒 Creado: {new Date(t.creado_en).toLocaleString("es-CO")}</span>
                    <span>
                      ⏳ Vence SLA:{" "}
                      <strong style={{ color: isOverdue ? "var(--feedback-error-text)" : "inherit" }}>
                        {due.toLocaleString("es-CO")}
                      </strong>
                    </span>
                    {t.sla_cumplido !== null && t.sla_cumplido !== undefined && (
                      <span>
                        SLA cumplido:{" "}
                        <strong style={{ color: t.sla_cumplido ? "var(--status-available)" : "var(--feedback-error-text)" }}>
                          {t.sla_cumplido ? "SÍ" : "NO"}
                        </strong>
                      </span>
                    )}
                  </div>

                  {/* Acciones para el personal */}
                  {isStaff && t.estado !== "resuelto" && t.estado !== "cerrado" && (
                    <div style={{ display: "flex", gap: "0.5rem", marginTop: "0.5rem", flexWrap: "wrap" }}>
                      {t.estado === "abierto" && (
                        <button type="button" className="btn btn-secondary" onClick={() => void handleTake(t.id)}>
                          Tomar ticket
                        </button>
                      )}
                      {t.nivel_actual !== "N3" && (
                        <button type="button" className="btn btn-secondary" onClick={() => void handleEscalate(t.id)}>
                          Escalar a {t.nivel_actual === "N1" ? "N2" : "N3"}
                        </button>
                      )}
                      <button
                        type="button"
                        className="btn btn-primary"
                        onClick={() => {
                          setResolvingId(t.id);
                          setResolveNote("");
                        }}
                      >
                        Resolver ticket
                      </button>
                    </div>
                  )}

                  {/* Historial expandido si hay más de 1 entrada */}
                  {t.historial.length > 1 && (
                    <details style={{ marginTop: "0.5rem", fontSize: "0.82rem", color: "var(--text-secondary)" }}>
                      <summary style={{ cursor: "pointer", fontWeight: 600 }}>
                        Ver historial de auditoría ({t.historial.length} eventos)
                      </summary>
                      <ul style={{ margin: "0.4rem 0 0 1.2rem", padding: 0 }}>
                        {t.historial.map((h, idx) => (
                          <li key={idx} className="numero-tabular">
                            {new Date(h.fecha).toLocaleTimeString("es-CO")} · {h.a_estado.toUpperCase()} ({h.nivel})
                            {h.nota && ` — ${h.nota}`}
                          </li>
                        ))}
                      </ul>
                    </details>
                  )}
                </article>
              );
            })}
          </div>
        )}
      </section>

      {/* Modal / formulario para resolver ticket */}
      {resolvingId && (
        <div
          role="dialog"
          style={{
            position: "fixed",
            inset: 0,
            background: "rgba(0, 0, 0, 0.6)",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            padding: "1rem",
            zIndex: 100
          }}
        >
          <div className="panel-card" style={{ maxWidth: "480px", width: "100%" }}>
            <h3 style={{ marginTop: 0 }}>Resolver ticket de soporte</h3>
            <form onSubmit={handleResolveSubmit}>
              <div className="form-group">
                <label>Nota de resolución técnica</label>
                <textarea
                  rows={3}
                  value={resolveNote}
                  onChange={(e) => setResolveNote(e.target.value)}
                  placeholder="Detalla la acción ejecutada para solucionar el incidente."
                  required
                />
              </div>

              <div style={{ display: "flex", justifyContent: "flex-end", gap: "0.75rem" }}>
                <button
                  type="button"
                  className="btn btn-secondary"
                  onClick={() => setResolvingId(null)}
                >
                  Cancelar
                </button>
                <button type="submit" className="btn btn-primary">
                  Confirmar resolución
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </main>
  );
}
