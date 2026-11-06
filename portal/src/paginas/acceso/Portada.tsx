import { Link, Navigate } from "react-router-dom";
import { useSession } from "../../sesion/almacenSesion";
import "../../estilos/portada.css";

// La portada no consulta ningún servicio: así la base de datos sigue pausada mientras nadie
// ingrese ni abra el catálogo. Los próximos eventos se muestran como vitrina y llevan al catálogo,
// que sí consulta disponibilidad real.
// Portadas generadas y subidas a Cloudinary por datos-demo/imagenes.py (el nombre de la nube es público)
const NUBE = import.meta.env.VITE_CLOUDINARY_NUBE as string | undefined;
const portada = (slug: string) =>
  NUBE ? `https://res.cloudinary.com/${NUBE}/image/upload/f_auto,q_auto,w_800/exponexo/demo/evento-${slug}` : null;

const PROXIMOS_EVENTOS = [
  {
    nombre: "Feria de Innovación 2026",
    slug: "exponexo-innovacion-2026",
    fechas: "24 – 27 nov 2026",
    resumen: "Feria de innovación, tecnología y negocios.",
  },
  {
    nombre: "Feria de Manufactura 2027",
    slug: "exponexo-manufactura-2027",
    fechas: "9 – 12 mar 2027",
    resumen: "Manufactura, automatización e industria 4.0.",
  },
  {
    nombre: "Feria de Agroindustria 2027",
    slug: "exponexo-agroindustria-2027",
    fechas: "15 – 18 jun 2027",
    resumen: "Agroindustria, sostenibilidad y cadena de suministro.",
  },
];

const PERFILES = [
  {
    titulo: "Expositores",
    texto: "Elige tu stand en el plano del pabellón, págalo con QR y recibe la factura al instante.",
    base: "sqlserver",
  },
  {
    titulo: "Visitantes",
    texto: "Compra tu entrada con acceso por QR y agenda citas de negocios con las empresas.",
    base: "oracle",
  },
  {
    titulo: "Operación del recinto",
    texto: "Tickets de soporte con tiempos de atención y monitoreo de kioscos y torniquetes.",
    base: "mongodb",
  },
];

export function Portada() {
  const { user } = useSession();
  if (user) {
    return <Navigate to="/inicio" replace />;
  }

  return (
    <div className="portada">
      <section className="portada-hero">
        <div className="portada-contenido">
          <p className="portada-antetitulo">Recinto ferial y de convenciones</p>
          <h1>
            Tu feria, de la reserva{" "}
            <br />
            a la puerta de entrada
          </h1>
          <p className="portada-lead">
            Reserva stands, vende entradas, agenda reuniones de negocios y atiende la operación del
            recinto en una sola plataforma.
          </p>
          <div className="portada-acciones">
            <Link to="/eventos" className="btn btn-primary">
              Ver eventos
            </Link>
            <Link to="/ingreso" className="btn portada-btn-contorno">
              Ingresar
            </Link>
          </div>
          <ul className="portada-franja" aria-label="Servicios de la plataforma">
            <li data-base="sqlserver">Reservas y agenda</li>
            <li data-base="oracle">Pagos y facturación</li>
            <li data-base="mongodb">Soporte y monitoreo</li>
          </ul>
        </div>
      </section>

      <section className="container portada-seccion">
        <p className="portada-antetitulo">Para cada participante</p>
        <h2>Qué puedes hacer</h2>
        <div className="portada-perfiles">
          {PERFILES.map((perfil) => (
            <article key={perfil.titulo} className="portada-tarjeta" data-base={perfil.base}>
              <h3>{perfil.titulo}</h3>
              <p>{perfil.texto}</p>
            </article>
          ))}
        </div>
      </section>

      <section className="portada-eventos">
        <div className="container portada-seccion">
          <div className="portada-encabezado">
            <div>
              <p className="portada-antetitulo">Próximamente</p>
              <h2>Eventos destacados</h2>
            </div>
            <Link to="/eventos" className="portada-enlace">
              Ver todos →
            </Link>
          </div>
          <div className="portada-lista-eventos">
            {PROXIMOS_EVENTOS.map((evento) => (
              <article key={evento.nombre} className="portada-tarjeta portada-evento">
                {portada(evento.slug) && (
                  <img className="portada-evento__imagen" src={portada(evento.slug)!} alt="" loading="lazy" width={1200} height={630} />
                )}
                <span className="portada-fecha">{evento.fechas}</span>
                <h3>{evento.nombre}</h3>
                <p>{evento.resumen}</p>
                <Link to="/eventos" className="portada-enlace">
                  Ver stands y entradas →
                </Link>
              </article>
            ))}
          </div>
        </div>
      </section>

      <section className="container portada-seccion portada-cierre">
        <h2>¿Primera vez en la plataforma?</h2>
        <p>Crea tu cuenta de visitante o expositor; el ingreso se protege con verificación en dos pasos.</p>
        <Link to="/registro" className="btn btn-primary">
          Crear cuenta
        </Link>
      </section>
    </div>
  );
}
