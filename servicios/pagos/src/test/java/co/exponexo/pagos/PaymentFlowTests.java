package co.exponexo.pagos;

import static org.assertj.core.api.Assertions.assertThat;
import static org.mockito.ArgumentMatchers.anyString;
import static org.mockito.ArgumentMatchers.eq;
import static org.mockito.Mockito.when;
import static org.springframework.security.test.web.servlet.request.SecurityMockMvcRequestPostProcessors.jwt;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

import co.exponexo.pagos.bandeja.OutboxMessage;
import co.exponexo.pagos.bandeja.OutboxRepository;
import co.exponexo.pagos.clientes.IdentityReservationClient;
import co.exponexo.pagos.clientes.IdentityReservationClient.ReferenceAmount;
import co.exponexo.pagos.facturas.InvoiceRepository;
import co.exponexo.pagos.qr.QrCharge;
import co.exponexo.pagos.qr.QrChargeRepository;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import java.math.BigDecimal;
import java.time.OffsetDateTime;
import java.time.ZoneOffset;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.AutoConfigureMockMvc;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.http.MediaType;
import org.springframework.security.core.authority.SimpleGrantedAuthority;
import org.springframework.test.context.bean.override.mockito.MockitoBean;
import org.springframework.test.web.servlet.MockMvc;
import org.springframework.test.web.servlet.MvcResult;

@SpringBootTest
@AutoConfigureMockMvc
class PaymentFlowTests {

    @Autowired
    private MockMvc mockMvc;

    @Autowired
    private ObjectMapper objectMapper;

    @Autowired
    private InvoiceRepository invoiceRepository;

    @Autowired
    private QrChargeRepository qrChargeRepository;

    @Autowired
    private OutboxRepository outboxRepository;

    @MockitoBean
    private IdentityReservationClient reservationClient;

    @Test
    void healthIsPublicAndProtectedEndpointsRequireJwt() throws Exception {
        mockMvc.perform(get("/salud"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.estado").value("ok"));

        mockMvc.perform(get("/v1/facturas/mias"))
                .andExpect(status().isUnauthorized());
    }

    @Test
    void orderIdempotencyQrSignatureInvoiceAndOutboxFlow() throws Exception {
        String userId = "user-expositor-1";
        String reservaId = "res-stand-101";

        when(reservationClient.fetchReferenceAmount(eq("stand"), eq(reservaId), anyString()))
                .thenReturn(new ReferenceAmount(
                        reservaId,
                        "stand",
                        userId,
                        new BigDecimal("3570000.00"),
                        "pendiente_pago"
                ));

        // 1. Create payment order with Idempotency-Key
        MvcResult createRes1 = mockMvc.perform(post("/v1/ordenes")
                        .with(jwt().jwt(j -> j.subject(userId).claim("rol", "expositor"))
                                .authorities(new SimpleGrantedAuthority("ROLE_EXPOSITOR")))
                        .header("Idempotency-Key", "idem-orden-101")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content("{\"referencia\":\"" + reservaId + "\",\"origen\":\"stand\"}"))
                .andExpect(status().isCreated())
                .andExpect(jsonPath("$.monto").value(3570000.00))
                .andExpect(jsonPath("$.estado").value("pendiente"))
                .andReturn();

        JsonNode orderJson = objectMapper.readTree(createRes1.getResponse().getContentAsString());
        String orderId = orderJson.get("id").asText();

        // 2. Repeating with same Idempotency-Key returns the exact same order id
        mockMvc.perform(post("/v1/ordenes")
                        .with(jwt().jwt(j -> j.subject(userId).claim("rol", "expositor"))
                                .authorities(new SimpleGrantedAuthority("ROLE_EXPOSITOR")))
                        .header("Idempotency-Key", "idem-orden-101")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content("{\"referencia\":\"" + reservaId + "\",\"origen\":\"stand\"}"))
                .andExpect(status().isCreated())
                .andExpect(jsonPath("$.id").value(orderId));

        // 3. Generate signed QR charge
        MvcResult qrRes = mockMvc.perform(post("/v1/ordenes/" + orderId + "/qr")
                        .with(jwt().jwt(j -> j.subject(userId).claim("rol", "expositor"))
                                .authorities(new SimpleGrantedAuthority("ROLE_EXPOSITOR"))))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.estado").value("vigente"))
                .andReturn();

        String qrPayload = objectMapper.readTree(qrRes.getResponse().getContentAsString())
                .get("contenido_qr").asText();

        // 4. Tampered QR signature must be rejected with 400
        mockMvc.perform(post("/v1/ordenes/" + orderId + "/pagar")
                        .with(jwt().jwt(j -> j.subject(userId).claim("rol", "expositor"))
                                .authorities(new SimpleGrantedAuthority("ROLE_EXPOSITOR")))
                        .contentType(MediaType.APPLICATION_JSON)
                        .content("{\"contenido_qr\":\"" + qrPayload + "TAMPERED\"}"))
                .andExpect(status().isBadRequest());

        // 5. Approve payment with valid signed QR -> issues invoice and writes pago.aprobado
        MvcResult payRes1 = mockMvc.perform(post("/v1/ordenes/" + orderId + "/pagar")
                        .with(jwt().jwt(j -> j.subject(userId).claim("rol", "expositor"))
                                .authorities(new SimpleGrantedAuthority("ROLE_EXPOSITOR")))
                        .contentType(MediaType.APPLICATION_JSON)
                        .content("{\"contenido_qr\":\"" + qrPayload + "\",\"nit_cliente\":\"900123456-7\",\"razon_social\":\"TecnoFeria SAS\"}"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.factura.estado").value("emitida"))
                .andExpect(jsonPath("$.factura.total").value(3570000.00))
                .andExpect(jsonPath("$.factura.subtotal").value(3000000.00))
                .andExpect(jsonPath("$.factura.impuesto").value(570000.00))
                .andReturn();

        String invoiceNumber = objectMapper.readTree(payRes1.getResponse().getContentAsString())
                .get("factura").get("numero").asText();
        assertThat(invoiceNumber).startsWith("EXN-");

        // 6. Paying the same order a second time is idempotent (returns same invoice, does not create a second one)
        mockMvc.perform(post("/v1/ordenes/" + orderId + "/pagar")
                        .with(jwt().jwt(j -> j.subject(userId).claim("rol", "expositor"))
                                .authorities(new SimpleGrantedAuthority("ROLE_EXPOSITOR")))
                        .contentType(MediaType.APPLICATION_JSON)
                        .content("{}"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.factura.numero").value(invoiceNumber));

        assertThat(invoiceRepository.findByOrdenId(orderId)).isPresent();
        List<OutboxMessage> outboxEvents = outboxRepository.findByPublicadoEnIsNullOrderByCreadoEnAsc();
        assertThat(outboxEvents).anyMatch(e -> "pago.aprobado".equals(e.getTipo()) && e.getCarga().contains(invoiceNumber));

        // 7. Admin registers refund -> writes pago.reembolsado
        mockMvc.perform(post("/v1/ordenes/" + orderId + "/reembolsos")
                        .with(jwt().jwt(j -> j.subject("admin-1").claim("rol", "administrador"))
                                .authorities(new SimpleGrantedAuthority("ROLE_ADMINISTRADOR")))
                        .contentType(MediaType.APPLICATION_JSON)
                        .content("{\"monto\":3570000.00,\"motivo\":\"Cancelación de evento\"}"))
                .andExpect(status().isCreated())
                .andExpect(jsonPath("$.estado").value("aprobado"));

        List<OutboxMessage> afterRefund = outboxRepository.findByPublicadoEnIsNullOrderByCreadoEnAsc();
        assertThat(afterRefund).anyMatch(e -> "pago.reembolsado".equals(e.getTipo()));
    }

    @Test
    void expiredQrChargeIsRejectedWith410() throws Exception {
        String userId = "user-visitante-2";
        String entradaId = "ent-202";

        when(reservationClient.fetchReferenceAmount(eq("entrada"), eq(entradaId), anyString()))
                .thenReturn(new ReferenceAmount(
                        entradaId,
                        "entrada",
                        userId,
                        new BigDecimal("45000.00"),
                        "pendiente_pago"
                ));

        MvcResult createRes = mockMvc.perform(post("/v1/ordenes")
                        .with(jwt().jwt(j -> j.subject(userId).claim("rol", "visitante"))
                                .authorities(new SimpleGrantedAuthority("ROLE_VISITANTE")))
                        .header("Idempotency-Key", "idem-orden-202")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content("{\"referencia\":\"" + entradaId + "\",\"origen\":\"entrada\"}"))
                .andExpect(status().isCreated())
                .andReturn();

        String orderId = objectMapper.readTree(createRes.getResponse().getContentAsString())
                .get("id").asText();

        mockMvc.perform(post("/v1/ordenes/" + orderId + "/qr")
                        .with(jwt().jwt(j -> j.subject(userId).claim("rol", "visitante"))
                                .authorities(new SimpleGrantedAuthority("ROLE_VISITANTE"))))
                .andExpect(status().isOk());

        // Expire the QR in the database
        for (QrCharge qr : qrChargeRepository.findByOrdenIdOrderByVenceEnDesc(orderId)) {
            qr.setVenceEn(OffsetDateTime.now(ZoneOffset.UTC).minusMinutes(5));
            qrChargeRepository.save(qr);
        }

        mockMvc.perform(post("/v1/ordenes/" + orderId + "/pagar")
                        .with(jwt().jwt(j -> j.subject(userId).claim("rol", "visitante"))
                                .authorities(new SimpleGrantedAuthority("ROLE_VISITANTE")))
                        .contentType(MediaType.APPLICATION_JSON)
                        .content("{}"))
                .andExpect(status().isGone());
    }
}
