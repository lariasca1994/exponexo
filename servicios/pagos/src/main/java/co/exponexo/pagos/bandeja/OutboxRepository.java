package co.exponexo.pagos.bandeja;

import java.util.List;
import org.springframework.data.jpa.repository.JpaRepository;

public interface OutboxRepository extends JpaRepository<OutboxMessage, String> {
    List<OutboxMessage> findByPublicadoEnIsNullOrderByCreadoEnAsc();
}
