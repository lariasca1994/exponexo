package co.exponexo.pagos.ordenes;

import co.exponexo.pagos.bandeja.OutboxMessage;
import co.exponexo.pagos.bandeja.OutboxRepository;
import co.exponexo.pagos.clientes.IdentityReservationClient;
import co.exponexo.pagos.clientes.IdentityReservationClient.ReferenceAmount;
import co.exponexo.pagos.config.ApiProblemException;
import co.exponexo.pagos.config.PagosProperties;
import co.exponexo.pagos.facturas.Invoice;
import co.exponexo.pagos.facturas.InvoiceLine;
import co.exponexo.pagos.facturas.InvoiceLineRepository;
import co.exponexo.pagos.facturas.InvoiceRepository;
import co.exponexo.pagos.qr.QrCharge;
import co.exponexo.pagos.qr.QrChargeRepository;
import co.exponexo.pagos.qr.QrSigningService;
import co.exponexo.pagos.reembolsos.Refund;
import co.exponexo.pagos.reembolsos.RefundRepository;
import java.math.BigDecimal;
import java.math.RoundingMode;
import java.sql.CallableStatement;
import java.sql.Types;
import java.time.OffsetDateTime;
import java.time.ZoneOffset;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.UUID;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

@Service
public class PaymentBillingService {

    public record QrGeneratedView(
            String qrId,
            String ordenId,
            String contenidoQr,
            String contenidoHuella,
            OffsetDateTime venceEn,
            String estado
    ) {}

    public record InvoiceDetailView(
            Invoice factura,
            List<InvoiceLine> detalles
    ) {}

    private final PaymentOrderRepository orderRepository;
    private final PaymentTransactionRepository transactionRepository;
    private final QrChargeRepository qrChargeRepository;
    private final InvoiceRepository invoiceRepository;
    private final InvoiceLineRepository invoiceLineRepository;
    private final RefundRepository refundRepository;
    private final OutboxRepository outboxRepository;
    private final QrSigningService qrSigningService;
    private final IdentityReservationClient reservationClient;
    private final PagosProperties properties;
    private final JdbcTemplate jdbcTemplate;

    public PaymentBillingService(
            PaymentOrderRepository orderRepository,
            PaymentTransactionRepository transactionRepository,
            QrChargeRepository qrChargeRepository,
            InvoiceRepository invoiceRepository,
            InvoiceLineRepository invoiceLineRepository,
            RefundRepository refundRepository,
            OutboxRepository outboxRepository,
            QrSigningService qrSigningService,
            IdentityReservationClient reservationClient,
            PagosProperties properties,
            JdbcTemplate jdbcTemplate
    ) {
        this.orderRepository = orderRepository;
        this.transactionRepository = transactionRepository;
        this.qrChargeRepository = qrChargeRepository;
        this.invoiceRepository = invoiceRepository;
        this.invoiceLineRepository = invoiceLineRepository;
        this.refundRepository = refundRepository;
        this.outboxRepository = outboxRepository;
        this.qrSigningService = qrSigningService;
        this.reservationClient = reservationClient;
        this.properties = properties;
        this.jdbcTemplate = jdbcTemplate;
    }

    @Transactional
    public PaymentOrder createOrder(
            String userId,
            String referencia,
            String origen,
            String idempotencyKey,
            String correlationId
    ) {
        if (idempotencyKey == null || idempotencyKey.isBlank()) {
            throw new ApiProblemException(
                    400,
                    "Cabecera Idempotency-Key requerida",
                    "Toda creación de orden exige la cabecera Idempotency-Key.",
                    "https://exponexo.co/problemas/idempotency-key-requerida"
            );
        }
        String cleanKey = idempotencyKey.trim();
        Optional<PaymentOrder> existing = orderRepository.findByClaveIdempotencia(cleanKey);
        if (existing.isPresent()) {
            return existing.get();
        }

        if (!"stand".equals(origen) && !"entrada".equals(origen)) {
            throw new ApiProblemException(
                    422,
                    "Origen inválido",
                    "El origen de la orden debe ser 'stand' o 'entrada'.",
                    "https://exponexo.co/problemas/origen-invalido"
            );
        }

        // Obtain the official amount from identidad-reservas (never trust client input)
        ReferenceAmount refAmount = reservationClient.fetchReferenceAmount(origen, referencia, correlationId);
        if (!"pendiente_pago".equals(refAmount.estado())) {
            throw new ApiProblemException(
                    409,
                    "Referencia no pagable",
                    "La reserva o entrada no está en estado pendiente de pago.",
                    "https://exponexo.co/problemas/referencia-no-pagable"
            );
        }
        if (!refAmount.usuarioId().isBlank() && !refAmount.usuarioId().equals(userId)) {
            throw new ApiProblemException(
                    403,
                    "Referencia ajena",
                    "No puedes crear una orden de pago para una reserva de otro usuario.",
                    "https://exponexo.co/problemas/referencia-ajena"
            );
        }

        OffsetDateTime now = OffsetDateTime.now(ZoneOffset.UTC);
        PaymentOrder order = new PaymentOrder();
        order.setId(UUID.randomUUID().toString());
        order.setReferencia(referencia);
        order.setOrigen(origen);
        order.setUsuarioId(userId);
        order.setMonto(refAmount.monto().setScale(2, RoundingMode.HALF_UP));
        order.setMoneda(properties.getInvoice().getCurrency());
        order.setEstado("pendiente");
        order.setClaveIdempotencia(cleanKey);
        order.setCreadaEn(now);
        order.setActualizadaEn(now);

        return orderRepository.save(order);
    }

    @Transactional(readOnly = true)
    public PaymentOrder getOrderForUser(String orderId, String userId, boolean isAdmin) {
        PaymentOrder order = orderRepository.findById(orderId)
                .orElseThrow(() -> new ApiProblemException(
                        404,
                        "Orden no encontrada",
                        "No existe la orden de pago solicitada.",
                        "https://exponexo.co/problemas/orden-no-encontrada"
                ));
        if (!isAdmin && !order.getUsuarioId().equals(userId)) {
            throw new ApiProblemException(
                    403,
                    "Acceso denegado",
                    "No tienes permiso para ver esta orden de pago.",
                    "https://exponexo.co/problemas/acceso-denegado"
            );
        }
        return order;
    }

    @Transactional
    public QrGeneratedView generateQrCharge(String orderId, String userId, boolean isAdmin) {
        PaymentOrder order = getOrderForUser(orderId, userId, isAdmin);
        if (!"creada".equals(order.getEstado()) && !"pendiente".equals(order.getEstado())) {
            throw new ApiProblemException(
                    409,
                    "Orden no admite cobro QR",
                    "La orden ya fue pagada, rechazada o reembolsada.",
                    "https://exponexo.co/problemas/orden-no-pagable"
            );
        }

        OffsetDateTime now = OffsetDateTime.now(ZoneOffset.UTC);
        // Mark any previous QR charges for this order as expired
        for (QrCharge prev : qrChargeRepository.findByOrdenIdOrderByVenceEnDesc(orderId)) {
            if ("vigente".equals(prev.getEstado())) {
                prev.setEstado("vencido");
                qrChargeRepository.save(prev);
            }
        }

        OffsetDateTime expiresAt = now.plusMinutes(properties.getQr().getExpirationMinutes());
        String signedPayload = qrSigningService.buildSignedPayload(
                order.getId(),
                order.getMonto(),
                order.getMoneda(),
                expiresAt
        );
        String fingerprint = qrSigningService.sha256Hex(signedPayload);

        QrCharge qr = new QrCharge();
        qr.setId(UUID.randomUUID().toString());
        qr.setOrdenId(order.getId());
        qr.setContenidoHuella(fingerprint);
        qr.setVenceEn(expiresAt);
        qr.setEstado("vigente");
        qrChargeRepository.save(qr);

        return new QrGeneratedView(
                qr.getId(),
                order.getId(),
                signedPayload,
                fingerprint,
                expiresAt,
                qr.getEstado()
        );
    }

    @Transactional
    public InvoiceDetailView approvePaymentAndIssueInvoice(
            String orderId,
            String userId,
            boolean isAdmin,
            String qrContent,
            String nitCliente,
            String razonSocial,
            String correlationId
    ) {
        PaymentOrder order = getOrderForUser(orderId, userId, isAdmin);

        // Idempotency: if order is already approved, return the existing invoice without creating a second one!
        if ("aprobada".equals(order.getEstado())) {
            Invoice existingInvoice = invoiceRepository.findByOrdenId(order.getId())
                    .orElseThrow(() -> new ApiProblemException(
                            500,
                            "Factura inconsistente",
                            "La orden figura aprobada pero no se encontró su factura.",
                            "https://exponexo.co/problemas/factura-no-encontrada"
                    ));
            List<InvoiceLine> lines = invoiceLineRepository.findByFacturaId(existingInvoice.getId());
            return new InvoiceDetailView(existingInvoice, lines);
        }

        if (!"creada".equals(order.getEstado()) && !"pendiente".equals(order.getEstado())) {
            throw new ApiProblemException(
                    409,
                    "Orden no pagable",
                    "La orden no está en estado pendiente.",
                    "https://exponexo.co/problemas/orden-no-pagable"
            );
        }

        OffsetDateTime now = OffsetDateTime.now(ZoneOffset.UTC);
        List<QrCharge> charges = qrChargeRepository.findByOrdenIdOrderByVenceEnDesc(order.getId());
        QrCharge latestQr = charges.stream()
                .filter(c -> "vigente".equals(c.getEstado()))
                .findFirst()
                .orElseThrow(() -> new ApiProblemException(
                        400,
                        "Sin cobro QR vigente",
                        "Debes generar un código QR vigente antes de pagar la orden.",
                        "https://exponexo.co/problemas/qr-no-generado"
                ));

        if (latestQr.getVenceEn().isBefore(now)) {
            latestQr.setEstado("vencido");
            qrChargeRepository.save(latestQr);
            throw new ApiProblemException(
                    410,
                    "Código QR vencido",
                    "El código QR ha expirado. Genera uno nuevo para continuar.",
                    "https://exponexo.co/problemas/qr-vencido"
            );
        }

        if (qrContent != null && !qrContent.isBlank()) {
            if (!qrSigningService.verifySignedPayload(qrContent)
                    || !qrSigningService.sha256Hex(qrContent).equals(latestQr.getContenidoHuella())) {
                throw new ApiProblemException(
                        400,
                        "Firma de QR inválida",
                        "El contenido del código QR fue alterado o no corresponde al cobro vigente.",
                        "https://exponexo.co/problemas/qr-alterado"
                );
            }
        }

        String cleanNit = (nitCliente != null && !nitCliente.isBlank()) ? nitCliente.trim() : "900000000-1";
        String cleanRazon = (razonSocial != null && !razonSocial.isBlank()) ? razonSocial.trim() : "Cliente ExpoNexo";
        String itemDesc = ("stand".equals(order.getOrigen()) ? "Reserva de stand · Ref " : "Entrada a evento · Ref ")
                + order.getReferencia();

        // Record transaction attempt
        PaymentTransaction tx = new PaymentTransaction();
        tx.setId(UUID.randomUUID().toString());
        tx.setOrdenId(order.getId());
        tx.setMetodo("qr");
        tx.setEstado("aprobada");
        tx.setCodigoAutorizacion("AUTH-" + UUID.randomUUID().toString().substring(0, 8).toUpperCase());
        tx.setOcurridaEn(now);
        transactionRepository.save(tx);

        String invoiceId = UUID.randomUUID().toString();
        String lineId = UUID.randomUUID().toString();
        String outboxEventId = UUID.randomUUID().toString();

        if (isOracleDatabase()) {
            jdbcTemplate.execute(
                    conn -> {
                        CallableStatement cs = conn.prepareCall(
                                "{call pkg_facturacion.emitir_factura(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)}"
                        );
                        cs.setString(1, order.getId());
                        cs.setString(2, invoiceId);
                        cs.setString(3, lineId);
                        cs.setString(4, properties.getInvoice().getPrefix());
                        cs.setString(5, cleanNit);
                        cs.setString(6, cleanRazon);
                        cs.setString(7, itemDesc);
                        cs.setBigDecimal(8, properties.getInvoice().getTaxPercentage());
                        cs.setString(9, outboxEventId);
                        cs.setString(10, correlationId);
                        cs.registerOutParameter(11, Types.VARCHAR);
                        return cs;
                    },
                    (CallableStatement cs) -> {
                        cs.execute();
                        return cs.getString(11);
                    }
            );
            Invoice oracleInvoice = invoiceRepository.findById(invoiceId).orElseThrow();
            List<InvoiceLine> oracleLines = invoiceLineRepository.findByFacturaId(invoiceId);
            return new InvoiceDetailView(oracleInvoice, oracleLines);
        }

        // Local / H2 Oracle-compatibility execution using `seq_numero_factura`
        Long seqVal = jdbcTemplate.queryForObject("SELECT NEXT VALUE FOR seq_numero_factura", Long.class);
        long consecutive = seqVal != null ? seqVal : 1L;
        String invoiceNumber = String.format("%s-%06d", properties.getInvoice().getPrefix(), consecutive);

        BigDecimal total = order.getMonto().setScale(2, RoundingMode.HALF_UP);
        BigDecimal divisor = BigDecimal.ONE.add(
                properties.getInvoice().getTaxPercentage().divide(new BigDecimal("100"), 6, RoundingMode.HALF_UP)
        );
        BigDecimal subtotal = total.divide(divisor, 2, RoundingMode.HALF_UP);
        BigDecimal tax = total.subtract(subtotal).setScale(2, RoundingMode.HALF_UP);

        order.setEstado("aprobada");
        order.setActualizadaEn(now);
        orderRepository.save(order);

        latestQr.setEstado("pagado");
        qrChargeRepository.save(latestQr);

        Invoice invoice = new Invoice();
        invoice.setId(invoiceId);
        invoice.setOrdenId(order.getId());
        invoice.setNumero(invoiceNumber);
        invoice.setFecha(now);
        invoice.setNitCliente(cleanNit);
        invoice.setRazonSocial(cleanRazon);
        invoice.setSubtotal(subtotal);
        invoice.setImpuesto(tax);
        invoice.setTotal(total);
        invoice.setEstado("emitida");
        invoiceRepository.save(invoice);

        InvoiceLine line = new InvoiceLine();
        line.setId(lineId);
        line.setFacturaId(invoiceId);
        line.setDescripcion(itemDesc);
        line.setCantidad(new BigDecimal("1.00"));
        line.setValorUnitario(subtotal);
        line.setImpuesto(tax);
        invoiceLineRepository.save(line);

        OutboxMessage outbox = new OutboxMessage();
        outbox.setId(outboxEventId);
        outbox.setTipo("pago.aprobado");
        outbox.setCarga(String.format(
                "{\"orden_id\":\"%s\",\"referencia\":\"%s\",\"origen\":\"%s\",\"monto\":%s,\"numero_factura\":\"%s\",\"usuario_id\":\"%s\"}",
                order.getId(),
                order.getReferencia(),
                order.getOrigen(),
                total.toPlainString(),
                invoiceNumber,
                order.getUsuarioId()
        ));
        outbox.setCorrelacionId(correlationId);
        outbox.setCreadoEn(now);
        outbox.setIntentos(0);
        outboxRepository.save(outbox);

        return new InvoiceDetailView(invoice, List.of(line));
    }

    @Transactional
    public Refund registerRefund(
            String orderId,
            BigDecimal refundAmount,
            String reason,
            String correlationId
    ) {
        PaymentOrder order = orderRepository.findById(orderId)
                .orElseThrow(() -> new ApiProblemException(
                        404,
                        "Orden no encontrada",
                        "No se encontró la orden a reembolsar.",
                        "https://exponexo.co/problemas/orden-no-encontrada"
                ));

        if (!"aprobada".equals(order.getEstado())) {
            throw new ApiProblemException(
                    409,
                    "Orden no reembolsable",
                    "Solo se pueden reembolsar órdenes en estado aprobada.",
                    "https://exponexo.co/problemas/orden-no-reembolsable"
            );
        }

        BigDecimal scaledAmount = refundAmount.setScale(2, RoundingMode.HALF_UP);
        if (scaledAmount.compareTo(BigDecimal.ZERO) <= 0 || scaledAmount.compareTo(order.getMonto()) > 0) {
            throw new ApiProblemException(
                    422,
                    "Monto de reembolso inválido",
                    "El monto a reembolsar debe ser mayor a cero y no superar lo pagado.",
                    "https://exponexo.co/problemas/monto-reembolso-invalido"
            );
        }

        OffsetDateTime now = OffsetDateTime.now(ZoneOffset.UTC);
        String refundId = UUID.randomUUID().toString();
        String outboxId = UUID.randomUUID().toString();

        Refund refund = new Refund();
        refund.setId(refundId);
        refund.setOrdenId(order.getId());
        refund.setMonto(scaledAmount);
        refund.setMotivo(reason.trim());
        refund.setEstado("aprobado");
        refund.setCreadoEn(now);
        refundRepository.save(refund);

        order.setEstado("reembolsada");
        order.setActualizadaEn(now);
        orderRepository.save(order);

        invoiceRepository.findByOrdenId(order.getId()).ifPresent(inv -> {
            inv.setEstado("anulada");
            invoiceRepository.save(inv);
        });

        OutboxMessage outbox = new OutboxMessage();
        outbox.setId(outboxId);
        outbox.setTipo("pago.reembolsado");
        outbox.setCarga(String.format(
                "{\"orden_id\":\"%s\",\"referencia\":\"%s\",\"origen\":\"%s\",\"monto\":%s,\"usuario_id\":\"%s\"}",
                order.getId(),
                order.getReferencia(),
                order.getOrigen(),
                scaledAmount.toPlainString(),
                order.getUsuarioId()
        ));
        outbox.setCorrelacionId(correlationId);
        outbox.setCreadoEn(now);
        outbox.setIntentos(0);
        outboxRepository.save(outbox);

        return refund;
    }

    @Transactional(readOnly = true)
    public List<Invoice> listUserInvoices(String userId) {
        List<String> orderIds = orderRepository.findByUsuarioIdOrderByCreadaEnDesc(userId).stream()
                .map(PaymentOrder::getId)
                .toList();
        if (orderIds.isEmpty()) {
            return List.of();
        }
        return invoiceRepository.findByOrdenIdInOrderByFechaDesc(orderIds);
    }

    @Transactional(readOnly = true)
    public InvoiceDetailView getInvoiceByNumber(String numero, String userId, boolean isAdmin) {
        Invoice invoice = invoiceRepository.findByNumero(numero)
                .orElseThrow(() -> new ApiProblemException(
                        404,
                        "Factura no encontrada",
                        "No existe una factura con el número indicado.",
                        "https://exponexo.co/problemas/factura-no-encontrada"
                ));
        PaymentOrder order = getOrderForUser(invoice.getOrdenId(), userId, isAdmin);
        List<InvoiceLine> lines = invoiceLineRepository.findByFacturaId(invoice.getId());
        return new InvoiceDetailView(invoice, lines);
    }

    @Transactional(readOnly = true)
    public Map<String, Object> getAdminRevenueSummary() {
        List<PaymentOrder> allOrders = orderRepository.findAll();
        BigDecimal totalStand = allOrders.stream()
                .filter(o -> "aprobada".equals(o.getEstado()) && "stand".equals(o.getOrigen()))
                .map(PaymentOrder::getMonto)
                .reduce(BigDecimal.ZERO, BigDecimal::add);
        BigDecimal totalEntrada = allOrders.stream()
                .filter(o -> "aprobada".equals(o.getEstado()) && "entrada".equals(o.getOrigen()))
                .map(PaymentOrder::getMonto)
                .reduce(BigDecimal.ZERO, BigDecimal::add);
        long approvedCount = allOrders.stream().filter(o -> "aprobada".equals(o.getEstado())).count();

        return Map.of(
                "moneda", properties.getInvoice().getCurrency(),
                "ordenes_aprobadas", approvedCount,
                "ingresos_stands", totalStand.setScale(2, RoundingMode.HALF_UP),
                "ingresos_entradas", totalEntrada.setScale(2, RoundingMode.HALF_UP),
                "ingresos_totales", totalStand.add(totalEntrada).setScale(2, RoundingMode.HALF_UP)
        );
    }

    private boolean isOracleDatabase() {
        try {
            return jdbcTemplate.execute((java.sql.Connection conn) ->
                    conn.getMetaData().getDatabaseProductName().toLowerCase().contains("oracle")
            );
        } catch (Exception ex) {
            return false;
        }
    }
}
