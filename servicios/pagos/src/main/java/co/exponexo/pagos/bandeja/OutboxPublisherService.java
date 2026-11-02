package co.exponexo.pagos.bandeja;

import com.fasterxml.jackson.databind.ObjectMapper;
import java.time.OffsetDateTime;
import java.time.ZoneOffset;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.scheduling.annotation.Scheduled;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

@Service
public class OutboxPublisherService {

    private static final Logger log = LoggerFactory.getLogger(OutboxPublisherService.class);

    private final OutboxRepository outboxRepository;
    private final ObjectMapper objectMapper;

    public OutboxPublisherService(OutboxRepository outboxRepository, ObjectMapper objectMapper) {
        this.outboxRepository = outboxRepository;
        this.objectMapper = objectMapper;
    }

    @Scheduled(fixedDelayString = "${exponexo.pagos.outbox-intervalo-ms:15000}")
    @Transactional
    public int publishPendingMessages() {
        List<OutboxMessage> pending = outboxRepository.findByPublicadoEnIsNullOrderByCreadoEnAsc();
        int published = 0;
        for (OutboxMessage msg : pending) {
            try {
                Map<String, Object> envelope = new LinkedHashMap<>();
                envelope.put("id", msg.getId());
                envelope.put("tipo", msg.getTipo());
                envelope.put("version", 1);
                envelope.put("ocurrido_en", msg.getCreadoEn().toString());
                envelope.put("origen", "pagos");
                envelope.put("correlacion_id", msg.getCorrelacionId());
                envelope.put("datos", objectMapper.readValue(msg.getCarga(), Map.class));

                log.info("Evento outbox publicado [{}]: id={}", msg.getTipo(), msg.getId());
                msg.setPublicadoEn(OffsetDateTime.now(ZoneOffset.UTC));
                msg.setIntentos(msg.getIntentos() + 1);
                outboxRepository.save(msg);
                published++;
            } catch (Exception ex) {
                log.error("Fallo al publicar mensaje de bandeja {}: {}", msg.getId(), ex.getMessage());
                msg.setIntentos(msg.getIntentos() + 1);
                outboxRepository.save(msg);
            }
        }
        return published;
    }
}
