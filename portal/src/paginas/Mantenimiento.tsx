import { useEffect, useState } from "react";
import { comprobarServicio } from "../api/mantenimiento";

const INTERVALO_SEGUNDOS = 30;

// Pantalla propia cuando un servicio no responde: se recupera sola apenas el servicio vuelve.
export function Mantenimiento() {
  const [segundos, setSegundos] = useState(INTERVALO_SEGUNDOS);
  const [comprobando, setComprobando] = useState(false);
  // Sin internet en el equipo no es mantenimiento: la misma pantalla lo dice y reintenta al volver la red.
  const [sinRed, setSinRed] = useState(() => !navigator.onLine);

  useEffect(() => {
    const conRed = () => {
      setSinRed(false);
      setComprobando(true);
      void comprobarServicio().finally(() => setComprobando(false));
    };
    const desconectado = () => setSinRed(true);
    window.addEventListener("online", conRed);
    window.addEventListener("offline", desconectado);
    return () => {
      window.removeEventListener("online", conRed);
      window.removeEventListener("offline", desconectado);
    };
  }, []);

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
        <p className="mantenimiento__antetitulo">{sinRed ? "Sin señal" : "Mantenimiento"}</p>
        <h1>{sinRed ? "Sin conexión" : "Estamos preparando el recinto"}</h1>
        {sinRed ? (
          <p>
            Tu equipo no tiene internet, así que no se pueden consultar reservas, pagos ni entradas. La
            pantalla vuelve sola cuando haya red. Lo que hacías no se guardó a medias.
          </p>
        ) : (
          <p>
            Uno de nuestros servicios no responde en este momento. Puede estar despertando después de un
            rato sin uso: suele tardar menos de un minuto. Lo que hacías no se guardó a medias.
          </p>
        )}
        <p className="mantenimiento__cuenta">
          <svg viewBox="0 0 24 24" aria-hidden="true">
            <circle className="anillo-fondo" cx="12" cy="12" r="9" />
            <circle className="anillo-valor" cx="12" cy="12" r="9" pathLength={1} style={{ strokeDashoffset: comprobando ? 0 : 1 - segundos / INTERVALO_SEGUNDOS }} />
          </svg>
          {comprobando ? "Comprobando…" : `Nuevo intento en ${segundos} s`}
        </p>
        <button type="button" className="btn btn-primary" onClick={reintentar} disabled={comprobando}>
          Intentar ahora
        </button>
      </div>
    </section>
  );
}
