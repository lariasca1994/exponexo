package co.exponexo.pagos.qr;

import java.util.List;
import org.springframework.data.jpa.repository.JpaRepository;

public interface QrChargeRepository extends JpaRepository<QrCharge, String> {
    List<QrCharge> findByOrdenIdOrderByVenceEnDesc(String ordenId);
}
