package co.exponexo.pagos.clientes;

import co.exponexo.pagos.config.ApiProblemException;
import co.exponexo.pagos.config.PagosProperties;
import java.math.BigDecimal;
import java.util.Map;
import org.springframework.http.MediaType;
import org.springframework.stereotype.Component;
import org.springframework.web.client.RestClient;

@Component
public class IdentityReservationClient {

    public record ReferenceAmount(String referencia, String origen, String usuarioId, BigDecimal monto, String estado) {}

    private final RestClient restClient;
    private final PagosProperties properties;

    public IdentityReservationClient(PagosProperties properties) {
        this.properties = properties;
        this.restClient = RestClient.builder()
                .baseUrl(properties.getIdentidadUrl())
                .build();
    }

    @SuppressWarnings("unchecked")
    public ReferenceAmount fetchReferenceAmount(String origen, String referencia, String correlationId) {
        try {
            Map<String, Object> tokenRes = restClient.post()
                    .uri("/v1/sesion/servicio")
                    .contentType(MediaType.APPLICATION_JSON)
                    .body(Map.of(
                            "servicio", "pagos",
                            "secreto_interno", properties.getInternalSecret()
                    ))
                    .retrieve()
                    .body(Map.class);

            if (tokenRes == null || !tokenRes.containsKey("token_servicio")) {
                throw new ApiProblemException(
                        502,
                        "Error de autenticación interna",
                        "No se pudo obtener el token interno hacia identidad-reservas.",
                        "https://exponexo.co/problemas/error-comunicacion-interna"
                );
            }
            String serviceJwt = tokenRes.get("token_servicio").toString();
            String path = "entrada".equals(origen)
                    ? "/v1/interno/entradas/" + referencia
                    : "/v1/interno/reservas/" + referencia;

            Map<String, Object> refData = restClient.get()
                    .uri(path)
                    .header("Authorization", "Bearer " + serviceJwt)
                    .header("X-Correlation-Id", correlationId != null ? correlationId : "")
                    .retrieve()
                    .body(Map.class);

            if (refData == null || !refData.containsKey("monto")) {
                throw new ApiProblemException(
                        404,
                        "Referencia no encontrada",
                        "No se encontró la reserva o entrada en identidad-reservas.",
                        "https://exponexo.co/problemas/referencia-no-encontrada"
                );
            }

            BigDecimal amount = new BigDecimal(refData.get("monto").toString());
            String userId = refData.getOrDefault("usuario_id", "").toString();
            String state = refData.getOrDefault("estado", "pendiente_pago").toString();
            return new ReferenceAmount(referencia, origen, userId, amount, state);
        } catch (ApiProblemException ex) {
            throw ex;
        } catch (Exception ex) {
            throw new ApiProblemException(
                    502,
                    "No se pudo consultar la referencia",
                    "Error al consultar el monto en el servicio de reservas.",
                    "https://exponexo.co/problemas/error-consulta-reserva"
            );
        }
    }
}
