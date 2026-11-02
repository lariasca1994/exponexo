package co.exponexo.pagos.reembolsos;

import java.util.List;
import org.springframework.data.jpa.repository.JpaRepository;

public interface RefundRepository extends JpaRepository<Refund, String> {
    List<Refund> findByOrdenId(String ordenId);
}
