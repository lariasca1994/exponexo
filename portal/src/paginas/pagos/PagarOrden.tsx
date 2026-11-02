import React, { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import {
  paymentsApi,
  type InvoiceDetailResponse,
  type PaymentOrderItem,
  type QrChargeView
} from "../../api/clientePagos";

export function PagarOrden() {
  const { origen, referencia } = useParams<{
    origen: "stand" | "entrada";
    referencia: string;
  }>();

  const [orden, setOrden] = useState<PaymentOrderItem | null>(null);
  const [qr, setQr] = useState<QrChargeView | null>(null);
  const [facturaEmitida, setFacturaEmitida] = useState<InvoiceDetailResponse | null>(null);
  const [nitCliente, setNitCliente] = useState("900123456-7");
  const [razonSocial, setRazonSocial] = useState("Empresa Expositora SAS");
  const [cargando, setCargando] = useState(true);
  const [pagando, setPagando] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const inicializarOrden = async () => {
      if (!origen || !referencia) return;
      setCargando(true);
      setError(null);
      try {
        const nuevaOrden = await paymentsApi.createOrder({
          origen: origen as "stand" | "entrada",
          referencia
        });
        setOrden(nuevaOrden);
        if (nuevaOrden.estado === "creada" || nuevaOrden.estado === "pendiente") {
          const qrGenerado = await paymentsApi.generateQr(nuevaOrden.id);
          setQr(qrGenerado);
        }
      } catch (err) {
        setError(err instanceof Error ? err.message : "No se pudo crear la orden de pago.");
      } finally {
        setCargando(false);
      }
    };
    void inicializarOrden();
  }, [origen, referencia]);

  const handlePagarQr = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!orden || !qr) return;
    setError(null);
    setPagando(true);
    try {
      const resultado = await paymentsApi.payOrder(orden.id, {
        contenido_qr: qr.contenido_qr,
        nit_cliente: nitCliente,
        razon_social: razonSocial
      });
      setFacturaEmitida(resultado);
    } catch (err) {
      setError(err instanceof Error ? err.message : "No se pudo procesar el pago del QR.");
    } finally {
      setPagando(false);
    }
  };

  return (
    <div className="container">
      <h1 style={{ marginTop: 0 }}>Pago con QR y Facturación</h1>

      {error && <div className="alert alert-error">{error}</div>}
      {cargando && <div className="panel-card">Preparando orden de pago y código QR firmado…</div>}

      {!cargando && orden && !facturaEmitida && (
        <div className="grid-2">
          <div className="panel-card">
            <span className="badge">Orden #{orden.id.slice(0, 8)}</span>
            <h3>Resumen del cobro</h3>
            <p>
              <strong>Concepto:</strong>{" "}
              {orden.origen === "stand" ? "Reserva de Stand" : "Entrada a Evento"} (Ref:{" "}
              <code>{orden.referencia.slice(0, 8)}</code>)
            </p>
            <p style={{ fontSize: "1.3rem", fontWeight: 700 }}>
              Total a pagar: ${Number(orden.monto).toLocaleString()} {orden.moneda}
            </p>

            {qr && (
              <div
                style={{
                  background: "var(--bg-subtle)",
                  padding: "1rem",
                  borderRadius: "var(--radius-md)",
                  marginTop: "1rem"
                }}
              >
                <p style={{ margin: "0 0 0.5rem 0", fontWeight: 600 }}>
                  Código QR firmado (HMAC-SHA256)
                </p>
                <code style={{ fontSize: "0.78rem", wordBreak: "break-all" }}>
                  {qr.contenido_qr}
                </code>
                <p style={{ fontSize: "0.82rem", color: "var(--text-secondary)", marginBottom: 0 }}>
                  Vigente hasta: {new Date(qr.vence_en).toLocaleTimeString()}
                </p>
              </div>
            )}
          </div>

          <div className="panel-card">
            <h3>Datos de facturación electrónica</h3>
            <form onSubmit={handlePagarQr}>
              <div className="form-group">
                <label htmlFor="nit">NIT o Documento</label>
                <input
                  id="nit"
                  className="input-field"
                  required
                  value={nitCliente}
                  onChange={(e) => setNitCliente(e.target.value)}
                />
              </div>
              <div className="form-group">
                <label htmlFor="razon">Razón social o Nombre</label>
                <input
                  id="razon"
                  className="input-field"
                  required
                  value={razonSocial}
                  onChange={(e) => setRazonSocial(e.target.value)}
                />
              </div>
              <button
                type="submit"
                className="btn btn-primary"
                style={{ width: "100%" }}
                disabled={pagando || !qr}
              >
                {pagando ? "Aprobando pago y emitiendo factura…" : "Confirmar pago del QR"}
              </button>
            </form>
          </div>
        </div>
      )}

      {facturaEmitida && (
        <div className="panel-card">
          <div className="alert alert-success">
            Pago aprobado. Se emitió la factura <strong>{facturaEmitida.factura.numero}</strong> y
            se registró el evento <code>pago.aprobado</code> en la bandeja de salida.
          </div>
          <h3>Factura Electrónica {facturaEmitida.factura.numero}</h3>
          <p>
            <strong>Cliente:</strong> {facturaEmitida.factura.razon_social} (NIT{" "}
            {facturaEmitida.factura.nit_cliente})
          </p>
          <p>
            <strong>Subtotal:</strong> ${Number(facturaEmitida.factura.subtotal).toLocaleString()} ·{" "}
            <strong>IVA:</strong> ${Number(facturaEmitida.factura.impuesto).toLocaleString()} ·{" "}
            <strong>Total:</strong> ${Number(facturaEmitida.factura.total).toLocaleString()} COP
          </p>
          <div style={{ display: "flex", gap: "0.75rem", marginTop: "1rem" }}>
            <Link to="/facturas" className="btn btn-primary">
              Ver todas mis facturas
            </Link>
            <Link to="/reservas" className="btn btn-secondary">
              Volver a mis reservas
            </Link>
          </div>
        </div>
      )}
    </div>
  );
}
