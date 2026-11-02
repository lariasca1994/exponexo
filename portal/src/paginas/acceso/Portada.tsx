import { Link } from "react-router-dom";

export function Portada() {
  return (
    <div className="container">
      <section className="panel-card" style={{ marginBottom: "1.5rem" }}>
        <span className="badge">Plataforma del Recinto Ferial</span>
        <h1 style={{ fontSize: "2rem", margin: "0.75rem 0" }}>
          Conecta expositores, visitantes y operación en un solo lugar
        </h1>
        <p style={{ color: "var(--text-secondary)", maxWidth: "680px" }}>
          En ExpoNexo los expositores reservan y pagan sus stands con QR, los visitantes adquieren
          sus entradas y agendan citas de negocios, y el equipo del recinto gestiona tickets con SLA
          y monitorea kioscos en tiempo real.
        </p>
        <div style={{ display: "flex", gap: "0.85rem", marginTop: "1.25rem", flexWrap: "wrap" }}>
          <Link to="/ingreso" className="btn btn-primary">
            Ingresar a mi cuenta
          </Link>
          <Link to="/registro" className="btn btn-secondary">
            Crear cuenta
          </Link>
        </div>
      </section>

      <div className="grid-2">
        <div className="panel-card">
          <h3>Para Expositores</h3>
          <p style={{ color: "var(--text-secondary)" }}>
            Explora el plano de pabellones, reserva tu stand, paga con código QR verificable y
            recibe tu factura electrónica al instante.
          </p>
        </div>
        <div className="panel-card">
          <h3>Para Visitantes</h3>
          <p style={{ color: "var(--text-secondary)" }}>
            Compra tu entrada con código QR de acceso y agenda reuniones de negocios con las
            empresas expositoras.
          </p>
        </div>
      </div>
    </div>
  );
}
