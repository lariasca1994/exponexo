// Detección de servicio caído (regla del portafolio: pantalla de mantenimiento propia).
// Si un servicio no responde (falla de red o 502/503/504), el portal muestra la pantalla de
// mantenimiento y comprueba cada 30 s la salud de ese servicio; cuando vuelve, la quita.
// Nunca reintenta la acción del usuario, para no duplicarla.

type Oyente = (servicioCaido: string | null) => void;

const oyentes = new Set<Oyente>();
let servicioCaido: string | null = null;

function avisar(valor: string | null) {
  servicioCaido = valor;
  oyentes.forEach((oyente) => oyente(valor));
}

export function suscribirMantenimiento(oyente: Oyente): () => void {
  oyentes.add(oyente);
  oyente(servicioCaido);
  return () => oyentes.delete(oyente);
}

export async function fetchServicio(baseUrl: string, path: string, init?: RequestInit): Promise<Response> {
  let respuesta: Response;
  try {
    respuesta = await fetch(`${baseUrl}${path}`, init);
  } catch (error) {
    avisar(baseUrl);
    throw error;
  }
  if ([502, 503, 504].includes(respuesta.status)) {
    avisar(baseUrl);
  }
  return respuesta;
}

/** Comprueba la salud del servicio caído; devuelve true si ya responde. */
export async function comprobarServicio(): Promise<boolean> {
  if (!servicioCaido) return true;
  try {
    const respuesta = await fetch(`${servicioCaido}/salud`, { cache: "no-store" });
    if (respuesta.ok) {
      avisar(null);
      return true;
    }
  } catch {
    // Sigue sin responder
  }
  return false;
}
