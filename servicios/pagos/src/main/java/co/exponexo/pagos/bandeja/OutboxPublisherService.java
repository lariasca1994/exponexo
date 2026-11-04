package co.exponexo.pagos.bandeja;

import co.exponexo.pagos.config.PagosProperties;
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
import software.amazon.awssdk.http.urlconnection.UrlConnectionHttpClient;
import software.amazon.awssdk.services.sns.SnsClient;
import software.amazon.awssdk.services.sns.model.MessageAttributeValue;
import software.amazon.awssdk.services.sns.model.PublishRequest;
import tools.jackson.databind.ObjectMapper;

@Service
public class OutboxPublisherService {

    private static final Logger log = LoggerFactory.getLogger(OutboxPublisherService.class);

    private final OutboxRepository outboxRepository;
    private final ObjectMapper objectMapper;
    private final String topicArn;
    private SnsClient snsClient;

    public OutboxPublisherService(
            OutboxRepository outboxRepository, ObjectMapper objectMapper, PagosProperties properties) {
        this.outboxRepository = outboxRepository;
        this.objectMapper = objectMapper;
        this.topicArn = properties.getEvents().getSnsTopicArn();
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

                if (topicArn == null || topicArn.isBlank()) {
                    log.info("Outbox local simulado [{}]: id={}", msg.getTipo(), msg.getId());
                } else {
                    sns().publish(PublishRequest.builder()
                            .topicArn(topicArn)
                            .message(objectMapper.writeValueAsString(envelope))
                            .messageAttributes(Map.of("tipo", MessageAttributeValue.builder()
                                    .dataType("String").stringValue(msg.getTipo()).build()))
                            .build());
                }
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

    // Región y credenciales salen de AWS_REGION, AWS_ACCESS_KEY_ID y AWS_SECRET_ACCESS_KEY
    private synchronized SnsClient sns() {
        if (snsClient == null) {
            snsClient = SnsClient.builder().httpClient(UrlConnectionHttpClient.create()).build();
        }
        return snsClient;
    }
}
