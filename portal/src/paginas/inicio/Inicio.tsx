import { Link } from "react-router-dom";
import { useSession } from "../../sesion/almacenSesion";

const ROLE_MODULES: Record<
  string,
  Array<{ titulo: string; descripcion: string; fase: string; ruta: string; accion: string }>
> = {
  expositor: [
    {
      titulo: "Plano de pabellones y stands",
      descripcion: "Consulta disponibilidad en tiempo real y reserva tu stand en la cuadrícula.",
      fase: "Fase 2",
      ruta: "/eventos",
      accion: "Ver plano de stands"
    },
    {
      titulo: "Mis reservas y facturación",
      descripcion: "Consulta tus stands reservados, paga con código QR firmado y descarga facturas.",
      fase: "Fase 3",
      ruta: "/reservas",
      accion: "Gestionar mis reservas"
    },
    {
      titulo: "Agenda de citas de negocios",
      descripcion: "Define tus franjas de disponibilidad y acepta reuniones B2B con visitantes.",
      fase: "Fase 5",
      ruta: "/agenda",
      accion: "Abrir agenda de citas"
    },
    {
      titulo: "Mesa de ayuda y soporte en stand",
      descripcion: "Abre tickets técnicos de conectividad, electricidad o mobiliario con medición de SLA.",
      fase: "Fase 6",
      ruta: "/soporte/tickets",
      accion: "Abrir ticket de soporte"
    }
  ],
  visitante: [
    {
      titulo: "Eventos y entradas digitales",
      descripcion: "Explora ferias publicadas y adquiere tu entrada con código QR firmado fuera de línea.",
      fase: "Fase 5",
      ruta: "/mis-entradas",
      accion: "Ver mis entradas"
    },
    {
      titulo: "Rueda de negocios con expositores",
      descripcion: "Consulta los horarios libres de cada empresa y propón reuniones comerciales.",
      fase: "Fase 5",
      ruta: "/agenda",
      accion: "Agendar citas"
    },
    {
      titulo: "Mis facturas electrónicas",
      descripcion: "Comprobantes y facturas con numeración consecutiva legal EXN.",
      fase: "Fase 3",
      ruta: "/facturas",
      accion: "Consultar facturas"
    },
    {
      titulo: "Mesa de ayuda del visitante",
      descripcion: "Soporte para accesos, acreditaciones o incidencias dentro del recinto.",
      fase: "Fase 6",
      ruta: "/soporte/tickets",
      accion: "Pedir asistencia"
    }
  ],
  personal: [
    {
      titulo: "Control de acceso en puerta",
      descripcion: "Escaneo y validación criptográfica de códigos QR (detección de QR alterados o reutilizados).",
      fase: "Fase 5",
      ruta: "/puerta/validar-qr",
      accion: "Escanear en torniquete"
    },
    {
      titulo: "Bandeja de tickets y SLA",
      descripcion: "Atiende incidentes por prioridad y escala de nivel (N1 -> N2 -> N3) con avisos a Telegram.",
      fase: "Fase 6",
      ruta: "/soporte/tickets",
      accion: "Bandeja técnica"
    },
    {
      titulo: "Monitoreo de kioscos y pantallas",
      descripcion: "Supervisión de dispositivos del recinto y apertura automática de tickets ante caídas.",
      fase: "Fase 6",
      ruta: "/soporte/dispositivos",
      accion: "Ver dispositivos"
    }
  ],
  administrador: [
    {
      titulo: "Tablero ejecutivo del recinto",
      descripcion: "Métricas consolidadas de ocupación (Azure SQL), recaudo (Oracle) y soporte (MongoDB).",
      fase: "Fase 7",
      ruta: "/admin/tablero",
      accion: "Abrir tablero"
    },
    {
      titulo: "Administración del catálogo",
      descripcion: "Crea ferias, pabellones, cuadrículas de stands y salas de negocios.",
      fase: "Fase 2",
      ruta: "/admin/catalogo",
      accion: "Gestionar catálogo"
    },
    {
      titulo: "Mesa de ayuda global",
      descripcion: "Supervisión de tickets y cumplimiento de SLA en todo el recinto.",
      fase: "Fase 6",
      ruta: "/soporte/tickets",
      accion: "Ver mesa de ayuda"
    },
    {
      titulo: "Dispositivos del recinto",
      descripcion: "Kioscos de registro, torniquetes y pantallas informativas.",
      fase: "Fase 6",
      ruta: "/soporte/dispositivos",
      accion: "Monitoreo de recinto"
    }
  ]
};

export function Inicio() {
  const { user } = useSession();
  if (!user) return null;

  const modulos = ROLE_MODULES[user.rol] ?? ROLE_MODULES.visitante;

  return (
    <div className="container">
      <div className="panel-card" style={{ marginBottom: "1.5rem" }}>
        <span className="badge">Rol activo: {user.rol.toUpperCase()}</span>
        <h1 style={{ margin: "0.5rem 0" }}>Hola, {user.nombre}</h1>
        <p style={{ color: "var(--text-secondary)", margin: 0 }}>
          Sesión protegida con verificación en dos pasos (JWT RS256 en memoria). Explora los módulos
          habilitados para tu perfil o administra tu seguridad en cualquier momento.
        </p>
      </div>

      <div className="grid-2">
        <div className="panel-card" style={{ display: "flex", flexDirection: "column", justifyContent: "space-between" }}>
          <div>
            <span className="badge">Fase 1 · Seguridad</span>
            <h3>Seguridad de la cuenta y MFA</h3>
            <p style={{ color: "var(--text-secondary)" }}>
              Configura tu app autenticadora con código QR TOTP, gestiona tus llaves biométricas Passkey
              y genera códigos de respaldo de emergencia.
            </p>
          </div>
          <Link to="/perfil" className="btn btn-secondary">
            Configurar seguridad y MFA
          </Link>
        </div>

        {modulos.map((mod) => (
          <div key={mod.titulo} className="panel-card" style={{ display: "flex", flexDirection: "column", justifyContent: "space-between" }}>
            <div>
              <span className="badge">{mod.fase}</span>
              <h3>{mod.titulo}</h3>
              <p style={{ color: "var(--text-secondary)" }}>{mod.descripcion}</p>
            </div>
            <Link to={mod.ruta} className="btn btn-primary" style={{ marginTop: "1rem" }}>
              {mod.accion}
            </Link>
          </div>
        ))}
      </div>
    </div>
  );
}
