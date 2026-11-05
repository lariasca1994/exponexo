import { useEffect, useState } from "react";
import { comprobarServicio } from "../api/mantenimiento";

const INTERVALO_SEGUNDOS = 30;

// Pantalla propia cuando un servicio no responde: se recupera sola apenas el servicio vuelve.
export function Mantenimiento() {
  const [segundos, setSegundos] = useState(INTERVALO_SEGUNDOS);
  const [comprobando, setComprobando] = useState(false);

  useEffect(() => {
    const reloj = setInterval(() => {
      setSegundos((s) => {
        if (s > 1) return s - 1;
        setComprobando(true);
        void comprobarServicio().finally(() => setComprobando(false));
        return INTERVALO_SEGUNDOS;
      });
    }, 1000);
    return () => clearInterval(reloj);
  }, []);

  const reintentar = () => {
    setComprobando(true);
    void comprobarServicio().finally(() => {
      setComprobando(false);
      setSegundos(INTERVALO_SEGUNDOS);
    });
  };

  return (
    <section className="mantenimiento" role="status" aria-live="polite">
      <div className="mantenimiento__tarjeta">
        <div className="mantenimiento__icono" aria-hidden="true">
          <span />
          <span />
          <span />
        </div>
        <p className="mantenimiento__antetitulo">Mantenimiento</p>
        <h1>Estamos preparando el recinto</h1>
        <p>
          Uno de nuestros servicios no responde en este momento. Puede estar despertando después de un
          rato sin uso: suele tardar menos de un minuto. Lo que hacías no se guardó a medias.
        </p>
        <p className="mantenimiento__cuenta">
          {comprobando ? "Comprobando…" : `Nuevo intento en ${segundos} s`}
        </p>
        <button type="button" className="btn btn-primary" onClick={reintentar} disabled={comprobando}>
          Intentar ahora
        </button>
      </div>
    </section>
  );
}
