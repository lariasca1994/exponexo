import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { identityApi } from "../../api/clienteIdentidad";
import type { EventItem } from "../../tipos/identidad";

export function ListaEventos() {
  const [eventos, setEventos] = useState<EventItem[]>([]);
  const [cargando, setCargando] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const cargar = async () => {
      setCargando(true);
      try {
        const res = await identityApi.listEvents();
        setEventos(res.items);
      } catch (err) {
        setError(err instanceof Error ? err.message : "No se pudieron cargar los eventos.");
      } finally {
        setCargando(false);
      }
    };
    void cargar();
  }, []);

  return (
    <div className="container">
      <h1 style={{ marginTop: 0 }}>Eventos y Ferias Publicadas</h1>
      <p style={{ color: "var(--text-secondary)" }}>
        Selecciona un evento para explorar el plano de sus pabellones y el estado de cada stand en
        tiempo real.
      </p>

      {error && <div className="alert alert-error">{error}</div>}
      {cargando && <div className="panel-card">Cargando catálogo de eventos…</div>}

      {!cargando && eventos.length === 0 && (
        <div className="panel-card">
          Aún no hay eventos publicados. Un administrador puede crearlos desde Administración del
          catálogo.
        </div>
      )}

      <div className="grid-2">
        {eventos.map((ev) => (
          <div key={ev.id} className="panel-card">
            <span className="badge">{ev.estado.toUpperCase()}</span>
            <h3 style={{ marginBottom: "0.4rem" }}>{ev.nombre}</h3>
            <p style={{ color: "var(--text-secondary)", fontSize: "0.92rem" }}>
              {ev.descripcion || "Feria oficial en el recinto ExpoNexo."}
            </p>
            <p style={{ fontSize: "0.85rem", color: "var(--text-secondary)" }}>
              <strong>Fechas:</strong> {new Date(ev.inicio).toLocaleDateString()} –{" "}
              {new Date(ev.fin).toLocaleDateString()} · <strong>Aforo:</strong> {ev.aforo}
            </p>
            <Link to={`/eventos/${ev.id}/stands`} className="btn btn-primary">
              Ver plano de stands
            </Link>
          </div>
        ))}
      </div>
    </div>
  );
}
