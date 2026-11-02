package co.exponexo.pagos.ordenes;

import co.exponexo.pagos.config.CorrelationIdFilter;
import co.exponexo.pagos.facturas.Invoice;
import co.exponexo.pagos.ordenes.PaymentBillingService.InvoiceDetailView;
import co.exponexo.pagos.ordenes.PaymentBillingService.QrGeneratedView;
import co.exponexo.pagos.reembolsos.Refund;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.validation.Valid;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;
import java.math.BigDecimal;
import java.util.List;
import java.util.Map;
import org.springframework.http.HttpStatus;
import org.springframework.security.core.Authentication;
import org.springframework.security.oauth2.jwt.Jwt;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestHeader;
import org.springframework.web.bind.annotation.ResponseStatus;
import org.springframework.web.bind.annotation.RestController;

@RestController
public class PaymentController {

    public record CreateOrderRequest(
            @NotBlank String referencia,
            @NotBlank String origen
    ) {}

    public record PayOrderRequest(
            String contenidoQr,
            String nitCliente,
            String razonSocial
    ) {}

    public record RefundOrderRequest(
            @NotNull BigDecimal monto,
            @NotBlank String motivo
    ) {}

    private final PaymentBillingService billingService;

    public PaymentController(PaymentBillingService billingService) {
        this.billingService = billingService;
    }

    @GetMapping("/salud")
    public Map<String, String> health() {
        return Map.of("estado", "ok", "servicio", "pagos");
    }

    @PostMapping("/v1/ordenes")
    @ResponseStatus(HttpStatus.CREATED)
    public PaymentOrder createOrder(
            @Valid @RequestBody CreateOrderRequest payload,
            @RequestHeader(value = "Idempotency-Key", required = false) String idempotencyKey,
            Authentication authentication,
            HttpServletRequest request
    ) {
        String userId = authentication.getName();
        String correlationId = (String) request.getAttribute(CorrelationIdFilter.ATTRIBUTE_NAME);
        return billingService.createOrder(
                userId,
                payload.referencia(),
                payload.origen(),
                idempotencyKey,
                correlationId
        );
    }

    @GetMapping("/v1/ordenes/{id}")
    public PaymentOrder getOrder(
            @PathVariable String id,
            Authentication authentication
    ) {
        return billingService.getOrderForUser(id, authentication.getName(), isAdmin(authentication));
    }

    @PostMapping("/v1/ordenes/{id}/qr")
    public QrGeneratedView generateQr(
            @PathVariable String id,
            Authentication authentication
    ) {
        return billingService.generateQrCharge(id, authentication.getName(), isAdmin(authentication));
    }

    @PostMapping("/v1/ordenes/{id}/pagar")
    public InvoiceDetailView payOrder(
            @PathVariable String id,
            @RequestBody(required = false) PayOrderRequest payload,
            Authentication authentication,
            HttpServletRequest request
    ) {
        String correlationId = (String) request.getAttribute(CorrelationIdFilter.ATTRIBUTE_NAME);
        String qrContent = payload != null ? payload.contenidoQr() : null;
        String nit = payload != null ? payload.nitCliente() : null;
        String razon = payload != null ? payload.razonSocial() : null;
        return billingService.approvePaymentAndIssueInvoice(
                id,
                authentication.getName(),
                isAdmin(authentication),
                qrContent,
                nit,
                razon,
                correlationId
        );
    }

    @GetMapping("/v1/facturas/mias")
    public List<Invoice> listMyInvoices(Authentication authentication) {
        return billingService.listUserInvoices(authentication.getName());
    }

    @GetMapping("/v1/facturas/{numero}")
    public InvoiceDetailView getInvoiceByNumber(
            @PathVariable String numero,
            Authentication authentication
    ) {
        return billingService.getInvoiceByNumber(numero, authentication.getName(), isAdmin(authentication));
    }

    @PostMapping("/v1/ordenes/{id}/reembolsos")
    @ResponseStatus(HttpStatus.CREATED)
    public Refund refundOrder(
            @PathVariable String id,
            @Valid @RequestBody RefundOrderRequest payload,
            HttpServletRequest request
    ) {
        String correlationId = (String) request.getAttribute(CorrelationIdFilter.ATTRIBUTE_NAME);
        return billingService.registerRefund(id, payload.monto(), payload.motivo(), correlationId);
    }

    @GetMapping("/v1/admin/resumen")
    public Map<String, Object> adminSummary() {
        return billingService.getAdminRevenueSummary();
    }

    private boolean isAdmin(Authentication authentication) {
        if (authentication.getPrincipal() instanceof Jwt jwt) {
            return "administrador".equalsIgnoreCase(jwt.getClaimAsString("rol"));
        }
        return authentication.getAuthorities().stream()
                .anyMatch(a -> "ROLE_ADMINISTRADOR".equals(a.getAuthority()));
    }
}
