import { getInMemoryTokens, setInMemoryTokens } from "../sesion/almacenSesion";
import type {
  AppointmentItem,
  EventItem,
  FreeSlotItem,
  LoginStep1Response,
  PaginatedEventsResponse,
  PavilionItem,
  ProblemDetails,
  SecurityProfileResponse,
  StandReservationItem,
  StandStatusItem,
  TicketItem,
  TokenPairResponse,
  TotpSetupResponse,
  UserAccount,
  ValidateTicketQrResult
} from "../tipos/identidad";

const IDENTIDAD_BASE_URL =
  import.meta.env.VITE_IDENTIDAD_URL || "http://localhost:8001";

export class ApiClientError extends Error {
  status: number;
  correlationId?: string;

  constructor(message: string, status: number, correlationId?: string) {
    super(message);
    this.name = "ApiClientError";
    this.status = status;
    this.correlationId = correlationId;
  }
}

async function requestIdentity<T>(
  path: string,
  options: RequestInit = {},
  customBearerToken?: string
): Promise<T> {
  const headers = new Headers(options.headers);
  if (!headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json");
  }
  headers.set("X-Correlation-Id", crypto.randomUUID());

  const { accessToken, refreshToken } = getInMemoryTokens();
  const bearer = customBearerToken ?? accessToken;
  if (bearer) {
    headers.set("Authorization", `Bearer ${bearer}`);
  }

  let response = await fetch(`${IDENTIDAD_BASE_URL}${path}`, {
    ...options,
    headers
  });

  if (response.status === 401 && !customBearerToken && refreshToken && path !== "/v1/sesion/refrescar") {
    const refreshRes = await fetch(`${IDENTIDAD_BASE_URL}/v1/sesion/refrescar`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-Correlation-Id": crypto.randomUUID()
      },
      body: JSON.stringify({ token_refresco: refreshToken })
    });
    if (refreshRes.ok) {
      const refreshed: TokenPairResponse = await refreshRes.json();
      setInMemoryTokens(refreshed.token_acceso, refreshed.token_refresco);
      headers.set("Authorization", `Bearer ${refreshed.token_acceso}`);
      response = await fetch(`${IDENTIDAD_BASE_URL}${path}`, {
        ...options,
        headers
      });
    }
  }

  if (!response.ok) {
    let detail = "Ocurrió un error al comunicarse con el servicio.";
    let correlationId = response.headers.get("X-Correlation-Id") ?? undefined;
    try {
      const problem: ProblemDetails = await response.json();
      if (problem.detail) {
        detail = problem.detail;
      } else if (problem.title) {
        detail = problem.title;
      }
      if (problem.correlacion_id) {
        correlationId = problem.correlacion_id;
      }
    } catch {
      // Response is not JSON
    }
    throw new ApiClientError(detail, response.status, correlationId);
  }

  return (await response.json()) as T;
}

export const identityApi = {
  registerAccount(payload: {
    correo: string;
    nombre: string;
    contrasena: string;
    rol: "visitante" | "expositor";
  }) {
    return requestIdentity<UserAccount>("/v1/cuentas", {
      method: "POST",
      body: JSON.stringify(payload)
    });
  },

  confirmEmail(payload: { correo: string; codigo: string }) {
    return requestIdentity<UserAccount>("/v1/cuentas/confirmar-correo", {
      method: "POST",
      body: JSON.stringify(payload)
    });
  },

  loginStep1(payload: { correo: string; contrasena: string }) {
    return requestIdentity<LoginStep1Response>("/v1/sesion/ingreso", {
      method: "POST",
      body: JSON.stringify(payload)
    });
  },

  requestLoginEmailCode(mfaPassToken: string) {
    return requestIdentity<{ mensaje: string }>(
      "/v1/sesion/codigo-correo",
      { method: "POST" },
      mfaPassToken
    );
  },

  loginStep2(
    mfaPassToken: string,
    payload: { metodo: "app" | "correo" | "respaldo"; codigo: string }
  ) {
    return requestIdentity<TokenPairResponse>(
      "/v1/sesion/segundo-paso",
      {
        method: "POST",
        body: JSON.stringify(payload)
      },
      mfaPassToken
    );
  },

  logout(refreshToken: string) {
    return requestIdentity<{ mensaje: string }>("/v1/sesion/salir", {
      method: "POST",
      body: JSON.stringify({ token_refresco: refreshToken })
    });
  },

  getSecurityProfile() {
    return requestIdentity<SecurityProfileResponse>("/v1/perfil/seguridad");
  },

  startTotpSetup() {
    return requestIdentity<TotpSetupResponse>("/v1/perfil/mfa/app", {
      method: "POST"
    });
  },

  confirmTotpSetup(codigo: string) {
    return requestIdentity<SecurityProfileResponse>(
      "/v1/perfil/mfa/app/confirmar",
      {
        method: "POST",
        body: JSON.stringify({ codigo })
      }
    );
  },

  setPreferredMfa(tipo: "app" | "correo") {
    return requestIdentity<SecurityProfileResponse>("/v1/perfil/mfa/preferido", {
      method: "PUT",
      body: JSON.stringify({ tipo })
    });
  },

  generateBackupCodes() {
    return requestIdentity<{ codigos: string[] }>(
      "/v1/perfil/codigos-respaldo",
      { method: "POST" }
    );
  },

  // Fase 2: Catálogo y Reservas
  listEvents(pagina = 1, tamano = 20) {
    return requestIdentity<PaginatedEventsResponse>(
      `/v1/eventos?pagina=${pagina}&tamano=${tamano}`
    );
  },

  getEvent(slugOrId: string) {
    return requestIdentity<EventItem>(`/v1/eventos/${encodeURIComponent(slugOrId)}`);
  },

  getEventStands(eventIdOrSlug: string) {
    return requestIdentity<StandStatusItem[]>(
      `/v1/eventos/${encodeURIComponent(eventIdOrSlug)}/stands`
    );
  },

  listPavilions() {
    return requestIdentity<PavilionItem[]>("/v1/pabellones");
  },

  reserveStand(payload: { evento_id: string; stand_id: string }, idempotencyKey?: string) {
    return requestIdentity<StandReservationItem>("/v1/reservas", {
      method: "POST",
      headers: {
        "Idempotency-Key": idempotencyKey || crypto.randomUUID()
      },
      body: JSON.stringify(payload)
    });
  },

  listMyReservations() {
    return requestIdentity<StandReservationItem[]>("/v1/reservas/mias");
  },

  cancelReservation(reservationId: string) {
    return requestIdentity<StandReservationItem>(
      `/v1/reservas/${encodeURIComponent(reservationId)}`,
      { method: "DELETE" }
    );
  },

  adminCreateEvent(payload: {
    nombre: string;
    slug: string;
    descripcion: string;
    inicio: string;
    fin: string;
    estado: "borrador" | "publicado" | "en_curso";
    precio_entrada: string;
    aforo: number;
  }) {
    return requestIdentity<EventItem>("/v1/admin/eventos", {
      method: "POST",
      body: JSON.stringify(payload)
    });
  },

  adminCreatePavilion(payload: {
    nombre: string;
    capacidad_stands: number;
  }) {
    return requestIdentity<PavilionItem>("/v1/admin/pabellones", {
      method: "POST",
      body: JSON.stringify(payload)
    });
  },

  adminCreateStand(payload: {
    pabellon_id: string;
    codigo: string;
    metros_cuadrados: string;
    tipo: "basico" | "esquinero" | "isla";
    precio_base: string;
    fila: number;
    columna: number;
  }) {
    return requestIdentity("/v1/admin/stands", {
      method: "POST",
      body: JSON.stringify(payload)
    });
  },

  // Fase 5: Entradas y agenda de negocios
  purchaseTicket(eventId: string, tipo: "general" | "negocios" | "prensa") {
    return requestIdentity<TicketItem>(
      `/v1/eventos/${encodeURIComponent(eventId)}/entradas`,
      {
        method: "POST",
        body: JSON.stringify({ tipo })
      }
    );
  },

  listMyTickets() {
    return requestIdentity<TicketItem[]>("/v1/mis-entradas");
  },

  validateTicketQr(codigo_qr: string, dispositivo_id = "puerta-principal-01") {
    return requestIdentity<ValidateTicketQrResult>("/v1/entradas/validar-qr", {
      method: "POST",
      body: JSON.stringify({ codigo_qr, dispositivo_id })
    });
  },

  updateMyAvailability(eventId: string, bloques: { desde: string; hasta: string }[]) {
    return requestIdentity(
      `/v1/eventos/${encodeURIComponent(eventId)}/mi-disponibilidad`,
      {
        method: "PUT",
        body: JSON.stringify({ bloques })
      }
    );
  },

  listEventExhibitors(eventId: string) {
    return requestIdentity<
      { id: string; nombre_completo: string; empresa_nombre: string | null }[]
    >(`/v1/eventos/${encodeURIComponent(eventId)}/expositores`);
  },

  getExhibitorFreeSlots(eventId: string, exhibitorId: string) {
    return requestIdentity<FreeSlotItem[]>(
      `/v1/eventos/${encodeURIComponent(eventId)}/expositores/${encodeURIComponent(
        exhibitorId
      )}/huecos`
    );
  },

  proposeAppointment(payload: {
    evento_id: string;
    anfitrion_id: string;
    inicio: string;
    fin: string;
    mensaje?: string;
  }) {
    return requestIdentity<AppointmentItem>("/v1/citas", {
      method: "POST",
      body: JSON.stringify(payload)
    });
  },

  respondAppointment(appointmentId: string, decision: "aceptar" | "rechazar") {
    return requestIdentity<AppointmentItem>(
      `/v1/citas/${encodeURIComponent(appointmentId)}/responder`,
      {
        method: "POST",
        body: JSON.stringify({ decision })
      }
    );
  },

  listMyAppointments() {
    return requestIdentity<AppointmentItem[]>("/v1/mis-citas");
  },

  getAdminSummary() {
    return requestIdentity<{
      eventos_totales: number;
      stands_totales: number;
      stands_ocupados: number;
      stands_pagados: number;
      ocupacion_stands_porcentaje: number;
      entradas_emitidas: number;
      entradas_activas_o_usadas: number;
      entradas_validadas_puerta: number;
      citas_negocios_aceptadas: number;
    }>("/v1/admin/resumen");
  },

  async uploadImage(file: File, folder = "exponexo") {
    const formData = new FormData();
    formData.append("archivo", file);
    formData.append("carpeta", folder);

    const { accessToken } = getInMemoryTokens();
    const headers = new Headers();
    if (accessToken) {
      headers.set("Authorization", `Bearer ${accessToken}`);
    }
    headers.set("X-Correlation-Id", crypto.randomUUID());

    const res = await fetch(`${IDENTIDAD_BASE_URL}/v1/imagenes/subir`, {
      method: "POST",
      headers,
      body: formData
    });
    if (!res.ok) {
      throw new ApiClientError("Error al subir la imagen a Cloudinary.", res.status);
    }
    return (await res.json()) as { secure_url: string; public_id: string };
  }
};
