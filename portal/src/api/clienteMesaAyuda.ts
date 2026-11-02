import { getInMemoryTokens } from "../sesion/almacenSesion";
import type { ProblemDetails } from "../tipos/identidad";
import { ApiClientError } from "./clienteIdentidad";

const MESA_AYUDA_BASE_URL =
  import.meta.env.VITE_MESA_AYUDA_URL || "http://localhost:8003";

export interface TicketHistoryItem {
  fecha: string;
  actor_id: string;
  de_estado?: string | null;
  a_estado: string;
  nivel: "N1" | "N2" | "N3";
  nota?: string | null;
}

export interface TicketItem {
  id: string;
  numero: string;
  evento_id?: string | null;
  creado_por_id: string;
  ubicacion: string;
  categoria: string;
  prioridad: "baja" | "media" | "alta" | "critica";
  nivel_actual: "N1" | "N2" | "N3";
  estado: "abierto" | "en_atencion" | "escalado" | "resuelto" | "cerrado";
  asignado_a_id?: string | null;
  descripcion: string;
  sla_vence_en: string;
  sla_cumplido?: boolean | null;
  sla_alerta_emitida: boolean;
  historial: TicketHistoryItem[];
  creado_en: string;
}

export interface DeviceItem {
  id: string;
  codigo: string;
  tipo: "kiosco" | "pantalla" | "torniquete";
  ubicacion: string;
  estado: "en_linea" | "sin_reporte" | "mantenimiento";
  ultimo_reporte_en: string;
  version_firmware: string;
  ticket_abierto_id?: string | null;
}

export interface MesaAyudaAdminSummary {
  tickets_totales: number;
  tickets_abiertos: number;
  tickets_resueltos: number;
  por_prioridad: {
    baja: number;
    media: number;
    alta: number;
    critica: number;
  };
  cumplimiento_sla_porcentaje: number;
  dispositivos_totales: number;
  dispositivos_en_linea: number;
  dispositivos_sin_reporte: number;
}

async function requestMesaAyuda<T>(
  path: string,
  options: RequestInit = {}
): Promise<T> {
  const headers = new Headers(options.headers);
  if (!headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json");
  }
  headers.set("X-Correlation-Id", crypto.randomUUID());

  const { accessToken } = getInMemoryTokens();
  if (accessToken) {
    headers.set("Authorization", `Bearer ${accessToken}`);
  }

  const response = await fetch(`${MESA_AYUDA_BASE_URL}${path}`, {
    ...options,
    headers
  });

  if (!response.ok) {
    let detail = "Ocurrió un error en la mesa de ayuda.";
    let correlationId = response.headers.get("X-Correlation-Id") ?? undefined;
    try {
      const problem: ProblemDetails = await response.json();
      if (problem.detail) detail = problem.detail;
      else if (problem.title) detail = problem.title;
      if (problem.correlacion_id) correlationId = problem.correlacion_id;
    } catch {
      // Non-JSON response
    }
    throw new ApiClientError(detail, response.status, correlationId);
  }

  return (await response.json()) as T;
}

export const helpDeskApi = {
  createTicket(payload: {
    evento_id?: string;
    ubicacion: string;
    categoria: string;
    prioridad: "baja" | "media" | "alta" | "critica";
    descripcion: string;
  }) {
    return requestMesaAyuda<TicketItem>("/v1/tickets", {
      method: "POST",
      body: JSON.stringify(payload)
    });
  },

  listTickets(params?: { estado?: string; prioridad?: string; nivel?: string }) {
    const q = new URLSearchParams();
    if (params?.estado) q.set("estado", params.estado);
    if (params?.prioridad) q.set("prioridad", params.prioridad);
    if (params?.nivel) q.set("nivel", params.nivel);
    const qs = q.toString() ? `?${q.toString()}` : "";
    return requestMesaAyuda<TicketItem[]>(`/v1/tickets${qs}`);
  },

  getTicket(id: string) {
    return requestMesaAyuda<TicketItem>(`/v1/tickets/${encodeURIComponent(id)}`);
  },

  takeTicket(id: string) {
    return requestMesaAyuda<TicketItem>(
      `/v1/tickets/${encodeURIComponent(id)}/tomar`,
      { method: "POST" }
    );
  },

  escalateTicket(id: string, nota?: string) {
    return requestMesaAyuda<TicketItem>(
      `/v1/tickets/${encodeURIComponent(id)}/escalar`,
      {
        method: "POST",
        body: JSON.stringify({ nota: nota || "Escalamiento solicitado desde el portal" })
      }
    );
  },

  resolveTicket(id: string, nota: string) {
    return requestMesaAyuda<TicketItem>(
      `/v1/tickets/${encodeURIComponent(id)}/resolver`,
      {
        method: "POST",
        body: JSON.stringify({ nota })
      }
    );
  },

  listDevices() {
    return requestMesaAyuda<DeviceItem[]>("/v1/dispositivos");
  },

  triggerScanCycle() {
    return requestMesaAyuda<{
      dispositivos_caidos_detectados: number;
      sla_vencidos_detectados: number;
    }>("/v1/interno/monitoreo/ejecutar", { method: "POST" });
  },

  getAdminSummary() {
    return requestMesaAyuda<MesaAyudaAdminSummary>("/v1/admin/resumen");
  }
};
