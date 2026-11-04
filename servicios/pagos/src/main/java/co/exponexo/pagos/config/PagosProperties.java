package co.exponexo.pagos.config;

import java.math.BigDecimal;
import java.util.Arrays;
import java.util.List;
import org.springframework.boot.context.properties.ConfigurationProperties;

@ConfigurationProperties(prefix = "exponexo")
public class PagosProperties {

    private String portalUrl = "http://localhost:5173";
    private String corsAllowedOrigins = "http://localhost:5173";
    private String identidadUrl = "http://localhost:8001";
    private String internalSecret = "";
    private Jwt jwt = new Jwt();
    private Qr qr = new Qr();
    private Invoice invoice = new Invoice();
    private Events events = new Events();

    public static class Events {
        private String snsTopicArn = "";

        public String getSnsTopicArn() { return snsTopicArn; }
        public void setSnsTopicArn(String snsTopicArn) { this.snsTopicArn = snsTopicArn; }
    }

    public static class Jwt {
        private String issuer = "";
        private String audience = "";
        private String jwksUrl = "";

        public String getIssuer() { return issuer; }
        public void setIssuer(String issuer) { this.issuer = issuer; }
        public String getAudience() { return audience; }
        public void setAudience(String audience) { this.audience = audience; }
        public String getJwksUrl() { return jwksUrl; }
        public void setJwksUrl(String jwksUrl) { this.jwksUrl = jwksUrl; }
    }

    public static class Qr {
        private String signingKey = "";
        private int expirationMinutes = 15;

        public String getSigningKey() { return signingKey; }
        public void setSigningKey(String signingKey) { this.signingKey = signingKey; }
        public int getExpirationMinutes() { return expirationMinutes; }
        public void setExpirationMinutes(int expirationMinutes) { this.expirationMinutes = expirationMinutes; }
    }

    public static class Invoice {
        private String prefix = "EXN";
        private String currency = "COP";
        private BigDecimal taxPercentage = new BigDecimal("19.00");

        public String getPrefix() { return prefix; }
        public void setPrefix(String prefix) { this.prefix = prefix; }
        public String getCurrency() { return currency; }
        public void setCurrency(String currency) { this.currency = currency; }
        public BigDecimal getTaxPercentage() { return taxPercentage; }
        public void setTaxPercentage(BigDecimal taxPercentage) { this.taxPercentage = taxPercentage; }
    }

    public List<String> getCorsOriginsList() {
        return Arrays.stream(corsAllowedOrigins.split(","))
                .map(String::trim)
                .filter(s -> !s.isEmpty())
                .toList();
    }

    public String getPortalUrl() { return portalUrl; }
    public void setPortalUrl(String portalUrl) { this.portalUrl = portalUrl; }
    public String getCorsAllowedOrigins() { return corsAllowedOrigins; }
    public void setCorsAllowedOrigins(String corsAllowedOrigins) { this.corsAllowedOrigins = corsAllowedOrigins; }
    public String getIdentidadUrl() { return identidadUrl; }
    public void setIdentidadUrl(String identidadUrl) { this.identidadUrl = identidadUrl; }
    public String getInternalSecret() { return internalSecret; }
    public void setInternalSecret(String internalSecret) { this.internalSecret = internalSecret; }
    public Jwt getJwt() { return jwt; }
    public void setJwt(Jwt jwt) { this.jwt = jwt; }
    public Qr getQr() { return qr; }
    public void setQr(Qr qr) { this.qr = qr; }
    public Invoice getInvoice() { return invoice; }
    public void setInvoice(Invoice invoice) { this.invoice = invoice; }
    public Events getEvents() { return events; }
    public void setEvents(Events events) { this.events = events; }
}
