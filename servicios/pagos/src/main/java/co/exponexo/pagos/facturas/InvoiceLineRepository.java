package co.exponexo.pagos.facturas;

import java.util.List;
import org.springframework.data.jpa.repository.JpaRepository;

public interface InvoiceLineRepository extends JpaRepository<InvoiceLine, String> {
    List<InvoiceLine> findByFacturaId(String facturaId);
}
