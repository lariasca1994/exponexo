package co.exponexo.pagos.facturas;

import java.util.Collection;
import java.util.List;
import java.util.Optional;
import org.springframework.data.jpa.repository.JpaRepository;

public interface InvoiceRepository extends JpaRepository<Invoice, String> {
    Optional<Invoice> findByOrdenId(String ordenId);
    Optional<Invoice> findByNumero(String numero);
    List<Invoice> findByOrdenIdInOrderByFechaDesc(Collection<String> ordenIds);
}
