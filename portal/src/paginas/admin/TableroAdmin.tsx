import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { identityApi } from "../../api/clienteIdentidad";
import { helpDeskApi, type MesaAyudaAdminSummary } from "../../api/clienteMesaAyuda";
import { paymentsApi } from "../../api/clientePagos";

interface IdentidadSummary {
  eventos_totales: number;
  stands_totales: number;
  stands_ocupados: number;
  stands_pagados: number;
  ocupacion_stands_porcentaje: number;
  entradas_emitidas: number;
  entradas_activas_o_usadas: number;
  entradas_validadas_puerta: number;
  citas_negocios_aceptadas: number;
}

interface PagosSummary {
  recaudo_total: number;
  facturas_emitidas: number;
  desglose_por_origen: {
    stand?: number;
    reserva_stand?: number;
    entrada?: number;
  };
}

export function TableroAdmin() {
  const [identidad, setIdentidad] = useState<IdentidadSummary | null>(null);
  const [pagos, setPagos] = useState<PagosSummary | null>(null);
  const [mesa, setMesa] = useState<MesaAyudaAdminSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  async function loadDashboard() {
    setLoading(true);
    setError(null);
    try {
      const [idRes, pagRes, mesaRes] = await Promise.all([
        identityApi.getAdminSummary().catch(() => null),
        paymentsApi.getAdminSummary().catch(() => null),
        helpDeskApi.getAdminSummary().catch(() => null)
      ]);
      setIdentidad(idRes);
      setPagos(pagRes);
      setMesa(mesaRes);
    } catch {
      setError("No se pudieron cargar todos los indicadores del recinto.");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void loadDashboard();
  }, []);

  return (
    <main className="container" style={{ paddingBlock: "2rem" }}>
      <header
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          marginBottom: "1.75rem",
          flexWrap: "wrap",
          gap: "1rem"
        }}
      >
        <div>
          <span className="badge">Fase 7 · Tablero Ejecutivo Multi-Servicio</span>
          <h1 style={{ margin: "0.25rem 0 0 0" }}>Tablero del Recinto Ferial</h1>
        </div>
        <div style={{ display: "flex", gap: "0.75rem" }}>
          <button type="button" className="btn btn-secondary" onClick={() => void loadDashboard()}>
            Actualizar métricas
          </button>
          <Link to="/admin/catalogo" className="btn btn-secondary">
            Catálogo
          </Link>
          <Link to="/inicio" className="btn btn-secondary">
            Inicio
          </Link>
        </div>
      </header>

      {error && <div role="alert" className="alert alert-error">{error}</div>}

      {loading ? (
        <p>Consolidando métricas de Azure SQL, Oracle y MongoDB Atlas...</p>
      ) : (
        <div style={{ display: "grid", gap: "1.5rem" }}>
          {/* Fila 1: KPIs Principales */}
          <div className="grid-4">
            <div className="panel-card">
              <span className="badge">Ocupación Recinto</span>
              <h2 className="numero-tabular" style={{ margin: "0.5rem 0 0.25rem 0", fontSize: "2rem", color: "var(--brand-primary)" }}>
                {identidad?.ocupacion_stands_porcentaje ?? 0}%
              </h2>
              <p style={{ margin: 0, fontSize: "0.85rem", color: "var(--text-secondary)" }}>
                {identidad?.stands_ocupados ?? 0} de {identidad?.stands_totales ?? 0} stands reservados
              </p>
            </div>

            <div className="panel-card">
              <span className="badge badge-success">Recaudo Total</span>
              <h2 className="numero-tabular" style={{ margin: "0.5rem 0 0.25rem 0", fontSize: "2rem", color: "var(--status-available)" }}>
                ${(pagos?.recaudo_total ?? 0).toLocaleString("es-CO")}
              </h2>
              <p style={{ margin: 0, fontSize: "0.85rem", color: "var(--text-secondary)" }}>
                {pagos?.facturas_emitidas ?? 0} facturas emitidas
              </p>
            </div>

            <div className="panel-card">
              <span className="badge">Asistencia Puerta</span>
              <h2 className="numero-tabular" style={{ margin: "0.5rem 0 0.25rem 0", fontSize: "2rem", color: "var(--brand-accent)" }}>
                {identidad?.entradas_validadas_puerta ?? 0}
              </h2>
              <p style={{ margin: 0, fontSize: "0.85rem", color: "var(--text-secondary)" }}>
                De {identidad?.entradas_emitidas ?? 0} entradas vendidas
              </p>
            </div>

            <div className="panel-card">
              <span className="badge badge-warning">Cumplimiento SLA</span>
              <h2 className="numero-tabular" style={{ margin: "0.5rem 0 0.25rem 0", fontSize: "2rem", color: "var(--brand-accent)" }}>
                {mesa?.cumplimiento_sla_porcentaje ?? 100}%
              </h2>
              <p style={{ margin: 0, fontSize: "0.85rem", color: "var(--text-secondary)" }}>
                {mesa?.tickets_abiertos ?? 0} tickets abiertos
              </p>
            </div>
          </div>

          {/* Fila 2: Desglose por Servicio */}
          <div className="grid-3">
            {/* Servicio 1: Identidad y Reservas */}
            <section className="panel-card">
              <h3 style={{ marginTop: 0 }}>Catálogo y Citas B2B</h3>
              <p style={{ fontSize: "0.85rem", color: "var(--text-secondary)" }}>
                Base de datos: <strong>Azure SQL</strong>
              </p>
              <ul style={{ paddingLeft: "1.2rem", margin: "1rem 0", lineHeight: 1.8 }}>
                <li>Eventos publicados: <strong>{identidad?.eventos_totales ?? 0}</strong></li>
                <li>Stands pagados: <strong>{identidad?.stands_pagados ?? 0}</strong></li>
                <li>Entradas activas: <strong>{identidad?.entradas_activas_o_usadas ?? 0}</strong></li>
                <li>Citas de negocios concertadas: <strong>{identidad?.citas_negocios_aceptadas ?? 0}</strong></li>
              </ul>
              <Link to="/eventos" className="btn btn-secondary" style={{ width: "100%" }}>
                Ver plano y stands
              </Link>
            </section>

            {/* Servicio 2: Pagos y Facturación */}
            <section className="panel-card">
              <h3 style={{ marginTop: 0 }}>Facturación Electrónica</h3>
              <p style={{ fontSize: "0.85rem", color: "var(--text-secondary)" }}>
                Base de datos: <strong>Oracle Autonomous (OCI)</strong>
              </p>
              <ul style={{ paddingLeft: "1.2rem", margin: "1rem 0", lineHeight: 1.8 }}>
                <li>Moneda: <strong>COP (Pesos Colombianos)</strong></li>
                <li>Impuesto IVA aplicado: <strong>19.00%</strong></li>
                <li>Consecutivo legal: <strong>EXN-... (Secuencia Oracle)</strong></li>
                <li>Cobros por QR firmado: <strong>Vigencia 15 min</strong></li>
              </ul>
              <Link to="/facturas" className="btn btn-secondary" style={{ width: "100%" }}>
                Ver facturas emitidas
              </Link>
            </section>

            {/* Servicio 3: Mesa de Ayuda y Dispositivos */}
            <section className="panel-card">
              <h3 style={{ marginTop: 0 }}>SLA y Dispositivos</h3>
              <p style={{ fontSize: "0.85rem", color: "var(--text-secondary)" }}>
                Base de datos: <strong>MongoDB Atlas (Time Series)</strong>
              </p>
              <ul style={{ paddingLeft: "1.2rem", margin: "1rem 0", lineHeight: 1.8 }}>
                <li>Dispositivos en línea: <strong>{mesa?.dispositivos_en_linea ?? 0}</strong></li>
                <li>Dispositivos sin reporte: <strong>{mesa?.dispositivos_sin_reporte ?? 0}</strong></li>
                <li>Tickets resueltos: <strong>{mesa?.tickets_resueltos ?? 0}</strong></li>
                <li>Prioridad Crítica: <strong>{mesa?.por_prioridad.critica ?? 0}</strong></li>
              </ul>
              <Link to="/soporte/tickets" className="btn btn-secondary" style={{ width: "100%" }}>
                Ir a mesa de ayuda
              </Link>
            </section>
          </div>
        </div>
      )}
    </main>
  );
}
