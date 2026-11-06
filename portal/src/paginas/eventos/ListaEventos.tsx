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
          <article key={ev.id} className="panel-card tarjeta-evento">
            <div className="tarjeta-evento__imagen">
              {ev.imagen_url ? (
                <img src={ev.imagen_url} alt={`Portada de ${ev.nombre}`} loading="lazy" width={1200} height={630} />
              ) : (
                <span aria-hidden="true">{ev.nombre.replace(/^ExpoNexo\s+/i, "")}</span>
              )}
            </div>
            <div className="tarjeta-evento__cuerpo">
              <span className="badge badge-success">{ev.estado}</span>
              <h3>{ev.nombre.replace(/^ExpoNexo\s+/i, "")}</h3>
              <p className="texto-tenue">{ev.descripcion || "Feria oficial en el recinto ferial."}</p>
              <dl className="tarjeta-evento__datos">
                <div>
                  <dt>Fechas</dt>
                  <dd>
                    {new Date(ev.inicio).toLocaleDateString("es-CO")} – {new Date(ev.fin).toLocaleDateString("es-CO")}
                  </dd>
                </div>
                <div>
                  <dt>Aforo</dt>
                  <dd className="numero-tabular">{ev.aforo.toLocaleString("es-CO")}</dd>
                </div>
              </dl>
              <Link to={`/eventos/${ev.id}/stands`} className="btn btn-primary">
                Ver plano de stands
              </Link>
            </div>
          </article>
        ))}
      </div>
    </div>
  );
}
