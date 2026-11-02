package co.exponexo.pagos.ordenes;

import java.util.List;
import java.util.Optional;
import org.springframework.data.jpa.repository.JpaRepository;

public interface PaymentOrderRepository extends JpaRepository<PaymentOrder, String> {
    Optional<PaymentOrder> findByClaveIdempotencia(String claveIdempotencia);
    List<PaymentOrder> findByUsuarioIdOrderByCreadaEnDesc(String usuarioId);
}
