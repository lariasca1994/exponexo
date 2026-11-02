package co.exponexo.pagos.qr;

import co.exponexo.pagos.config.PagosProperties;
import java.math.BigDecimal;
import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.time.OffsetDateTime;
import java.util.Base64;
import java.util.HexFormat;
import javax.crypto.Mac;
import javax.crypto.spec.SecretKeySpec;
import org.springframework.stereotype.Service;

@Service
public class QrSigningService {

    private final PagosProperties properties;

    public QrSigningService(PagosProperties properties) {
        this.properties = properties;
    }

    public String buildSignedPayload(String orderId, BigDecimal amount, String currency, OffsetDateTime expiresAt) {
        String baseData = String.format(
                "EXPONEXO|ORD=%s|AMT=%s|CUR=%s|EXP=%d",
                orderId,
                amount.toPlainString(),
                currency,
                expiresAt.toEpochSecond()
        );
        String signature = computeHmacBase64Url(baseData);
        return baseData + "|SIG=" + signature;
    }

    public boolean verifySignedPayload(String qrPayload) {
        int sigIndex = qrPayload.lastIndexOf("|SIG=");
        if (sigIndex <= 0) {
            return false;
        }
        String baseData = qrPayload.substring(0, sigIndex);
        String providedSig = qrPayload.substring(sigIndex + 5);
        String expectedSig = computeHmacBase64Url(baseData);
        return MessageDigest.isEqual(
                providedSig.getBytes(StandardCharsets.UTF_8),
                expectedSig.getBytes(StandardCharsets.UTF_8)
        );
    }

    public String sha256Hex(String input) {
        try {
            MessageDigest digest = MessageDigest.getInstance("SHA-256");
            byte[] hash = digest.digest(input.getBytes(StandardCharsets.UTF_8));
            return HexFormat.of().formatHex(hash);
        } catch (Exception ex) {
            throw new IllegalStateException("Error calculando huella SHA-256", ex);
        }
    }

    private String computeHmacBase64Url(String data) {
        try {
            Mac mac = Mac.getInstance("HmacSHA256");
            byte[] keyBytes = properties.getQr().getSigningKey().getBytes(StandardCharsets.UTF_8);
            mac.init(new SecretKeySpec(keyBytes, "HmacSHA256"));
            byte[] rawHmac = mac.doFinal(data.getBytes(StandardCharsets.UTF_8));
            return Base64.getUrlEncoder().withoutPadding().encodeToString(rawHmac);
        } catch (Exception ex) {
            throw new IllegalStateException("Error firmando contenido QR", ex);
        }
    }
}
