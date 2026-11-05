export type UserRole = "visitante" | "expositor" | "personal" | "administrador";

export interface UserAccount {
  id: string;
  correo: string;
  nombre: string;
  rol: UserRole;
  activo: boolean;
  correo_verificado: boolean;
  creado_en: string;
}

export interface LoginStep1Response {
  pase_segundo_paso: string;
  vence_en_segundos: number;
  metodos_disponibles: string[];
  metodo_preferido: string;
  requiere_configurar_mfa: boolean;
}

export interface TokenPairResponse {
  token_acceso: string;
  token_refresco: string;
  tipo_token: string;
  vence_en_segundos: number;
  usuario: UserAccount;
}

export interface MfaFactorInfo {
  tipo: "app" | "correo";
  activo: boolean;
  preferido: boolean;
  creado_en: string;
}

export interface PasskeyInfo {
  id: string;
  nombre_dispositivo: string;
  creada_en: string;
  ultimo_uso_en: string | null;
}

export interface SessionInfo {
  id: string;
  creada_en: string;
  vence_en: string;
  agente: string | null;
}

export interface SecurityProfileResponse {
  usuario: UserAccount;
  telegram_vinculado: boolean;
  metodos_mfa: MfaFactorInfo[];
  metodo_preferido: string | null;
  codigos_respaldo_disponibles: number;
  llaves_acceso: PasskeyInfo[];
  sesiones_activas: SessionInfo[];
}

export interface TotpSetupResponse {
  secreto: string;
  otpauth_url: string;
  qr_datos_url: string;
}

export interface ProblemDetails {
  type?: string;
  title?: string;
  status?: number;
  detail?: string;
  correlacion_id?: string;
}

export interface EventItem {
  id: string;
  nombre: string;
  slug: string;
  descripcion: string;
  inicio: string;
  fin: string;
  estado: string;
  precio_entrada: string;
  aforo: number;
  imagen_url?: string | null;
  creado_en: string;
}

export interface PaginatedEventsResponse {
  pagina: number;
  tamano: number;
  total: number;
  items: EventItem[];
}

export interface PavilionItem {
  id: string;
  nombre: string;
  capacidad_stands: number;
  plano_url: string | null;
}

export interface StandStatusItem {
  id: string;
  pabellon_id: string;
  pabellon_nombre: string;
  codigo: string;
  metros_cuadrados: string;
  tipo: "basico" | "esquinero" | "isla";
  precio_base: string;
  fila: number;
  columna: number;
  estado: "disponible" | "reservado" | "pagado";
}

export interface StandReservationItem {
  id: string;
  evento_id: string;
  stand_id: string;
  empresa_id: string | null;
  usuario_id: string;
  estado: "pendiente_pago" | "pagada" | "cancelada" | "vencida";
  monto: string;
  vence_en: string;
  orden_pago_id: string | null;
  creado_en: string;
}

export interface TicketItem {
  id: string;
  evento_id: string;
  evento_nombre: string | null;
  usuario_id: string;
  tipo: "general" | "negocios" | "prensa";
  estado: "pendiente_pago" | "activa" | "usada" | "cancelada";
  precio_sugerido: string;
  orden_pago_id: string | null;
  codigo_qr: string | null;
  usada_en: string | null;
  usada_en_dispositivo: string | null;
  creada_en: string;
}

export interface ValidateTicketQrResult {
  valida: boolean;
  entrada_id: string;
  evento_id: string;
  usuario_id: string;
  tipo: string;
  estado: string;
  usada_en: string;
  usada_en_dispositivo: string;
}

export interface FreeSlotItem {
  expositor_id: string;
  expositor_nombre: string;
  empresa_nombre: string | null;
  desde: string;
  hasta: string;
}

export interface AppointmentItem {
  id: string;
  evento_id: string;
  solicitante_id: string;
  solicitante_nombre: string | null;
  anfitrion_id: string;
  anfitrion_nombre: string | null;
  sala_id: string | null;
  sala_codigo: string | null;
  inicio: string;
  fin: string;
  estado: "propuesta" | "aceptada" | "rechazada" | "cancelada";
  mensaje: string | null;
  creada_en: string;
}
