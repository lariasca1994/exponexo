import { fetchServicio } from "./mantenimiento";
import { getInMemoryTokens } from "../sesion/almacenSesion";
import type { ProblemDetails } from "../tipos/identidad";
import { ApiClientError } from "./clienteIdentidad";

const PAGOS_BASE_URL =
  import.meta.env.VITE_PAGOS_URL || "http://localhost:8002";

export interface PaymentOrderItem {
  id: string;
  referencia: string;
  origen: "stand" | "entrada";
  usuario_id: string;
  monto: number;
  moneda: string;
  estado: "creada" | "pendiente" | "aprobada" | "rechazada" | "expirada" | "reembolsada";
  clave_idempotencia: string;
  creada_en: string;
  actualizada_en: string;
}

export interface QrChargeView {
  qr_id: string;
  orden_id: string;
  contenido_qr: string;
  contenido_huella: string;
  vence_en: string;
  estado: string;
}

export interface InvoiceItem {
  id: string;
  orden_id: string;
  numero: string;
  fecha: string;
  nit_cliente: string;
  razon_social: string;
  subtotal: number;
  impuesto: number;
  total: number;
  estado: "emitida" | "anulada";
}

export interface InvoiceLineItem {
  id: string;
  factura_id: string;
  descripcion: string;
  cantidad: number;
  valor_unitario: number;
  impuesto: number;
}

export interface InvoiceDetailResponse {
  factura: InvoiceItem;
  detalles: InvoiceLineItem[];
}

async function requestPayments<T>(
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

  const response = await fetchServicio(PAGOS_BASE_URL, path, {
    ...options,
    headers
  });

  if (!response.ok) {
    let detail = "Ocurrió un error al comunicarse con el servicio de pagos.";
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

export const paymentsApi = {
  createOrder(
    payload: { referencia: string; origen: "stand" | "entrada" },
    idempotencyKey?: string
  ) {
    return requestPayments<PaymentOrderItem>("/v1/ordenes", {
      method: "POST",
      headers: {
        "Idempotency-Key": idempotencyKey || `ord-${payload.origen}-${payload.referencia}`
      },
      body: JSON.stringify(payload)
    });
  },

  getOrder(orderId: string) {
    return requestPayments<PaymentOrderItem>(`/v1/ordenes/${encodeURIComponent(orderId)}`);
  },

  generateQr(orderId: string) {
    return requestPayments<QrChargeView>(
      `/v1/ordenes/${encodeURIComponent(orderId)}/qr`,
      { method: "POST" }
    );
  },

  payOrder(
    orderId: string,
    payload: { contenido_qr?: string; nit_cliente?: string; razon_social?: string }
  ) {
    return requestPayments<InvoiceDetailResponse>(
      `/v1/ordenes/${encodeURIComponent(orderId)}/pagar`,
      {
        method: "POST",
        body: JSON.stringify(payload)
      }
    );
  },

  listMyInvoices() {
    return requestPayments<InvoiceItem[]>("/v1/facturas/mias");
  },

  getInvoiceDetail(numero: string) {
    return requestPayments<InvoiceDetailResponse>(
      `/v1/facturas/${encodeURIComponent(numero)}`
    );
  },

  getAdminSummary() {
    return requestPayments<{
      recaudo_total: number;
      facturas_emitidas: number;
      desglose_por_origen: {
        stand?: number;
        reserva_stand?: number;
        entrada?: number;
      };
    }>("/v1/admin/resumen");
  }
};
