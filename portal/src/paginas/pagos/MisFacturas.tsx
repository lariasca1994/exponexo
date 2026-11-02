import { useEffect, useState } from "react";
import {
  paymentsApi,
  type InvoiceDetailResponse,
  type InvoiceItem
} from "../../api/clientePagos";

export function MisFacturas() {
  const [facturas, setFacturas] = useState<InvoiceItem[]>([]);
  const [detalle, setDetalle] = useState<InvoiceDetailResponse | null>(null);
  const [cargando, setCargando] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const cargar = async () => {
      setCargando(true);
      try {
        const data = await paymentsApi.listMyInvoices();
        setFacturas(data);
      } catch (err) {
        setError(err instanceof Error ? err.message : "No se pudieron cargar tus facturas.");
      } finally {
        setCargando(false);
      }
    };
    void cargar();
  }, []);

  const handleVerDetalle = async (numero: string) => {
    setError(null);
    try {
      const d = await paymentsApi.getInvoiceDetail(numero);
      setDetalle(d);
    } catch (err) {
      setError(err instanceof Error ? err.message : "No se pudo cargar el detalle de la factura.");
    }
  };

  return (
    <div className="container">
      <h1 style={{ marginTop: 0 }}>Mis Facturas</h1>

      {error && <div className="alert alert-error">{error}</div>}
      {cargando && <div className="panel-card">Cargando facturas emitidas…</div>}

      {!cargando && facturas.length === 0 && (
        <div className="panel-card">Aún no tienes facturas emitidas.</div>
      )}

      <div className="grid-2">
        <div>
          {facturas.map((f) => (
            <div key={f.id} className="panel-card" style={{ marginBottom: "1rem" }}>
              <span className="badge">{f.estado.toUpperCase()}</span>
              <h3 style={{ margin: "0.4rem 0" }}>Factura {f.numero}</h3>
              <p style={{ margin: "0.25rem 0" }}>
                <strong>Cliente:</strong> {f.razon_social} ({f.nit_cliente})
              </p>
              <p style={{ margin: "0.25rem 0" }}>
                <strong>Total:</strong> ${Number(f.total).toLocaleString()} COP
              </p>
              <button
                type="button"
                className="btn btn-secondary"
                style={{ marginTop: "0.5rem" }}
                onClick={() => handleVerDetalle(f.numero)}
              >
                Ver desglose
              </button>
            </div>
          ))}
        </div>

        {detalle && (
          <div className="panel-card">
            <h3 style={{ marginTop: 0 }}>Desglose · {detalle.factura.numero}</h3>
            <p>
              <strong>Fecha emisión:</strong> {new Date(detalle.factura.fecha).toLocaleString()}
            </p>
            <p>
              <strong>Subtotal:</strong> ${Number(detalle.factura.subtotal).toLocaleString()} COP
            </p>
            <p>
              <strong>Impuesto (IVA):</strong> ${Number(detalle.factura.impuesto).toLocaleString()}{" "}
              COP
            </p>
            <p style={{ fontSize: "1.1rem", fontWeight: 700 }}>
              Total: ${Number(detalle.factura.total).toLocaleString()} COP
            </p>
            <hr style={{ borderColor: "var(--border-color)" }} />
            <h4>Conceptos facturados</h4>
            <ul>
              {detalle.detalles.map((l) => (
                <li key={l.id}>
                  {l.descripcion} — Valor unitario: ${Number(l.valor_unitario).toLocaleString()} +
                  IVA ${Number(l.impuesto).toLocaleString()}
                </li>
              ))}
            </ul>
          </div>
        )}
      </div>
    </div>
  );
}
