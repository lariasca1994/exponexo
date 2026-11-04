package co.exponexo.pagos.config;

import java.net.URI;
import java.util.List;
import java.util.Locale;
import java.util.Arrays;
import org.springframework.boot.ApplicationArguments;
import org.springframework.boot.ApplicationRunner;
import org.springframework.core.env.Environment;
import org.springframework.stereotype.Component;

@Component
public class ProductionConfigurationValidator implements ApplicationRunner {

    private static final String DEVELOPMENT_INTERNAL_SECRET = "dev-interno-secreto";
    private static final String DEVELOPMENT_QR_KEY = "dev-qr-signing-key-32-bytes-minimum";
    private static final List<String> REQUIRED_ORACLE_SETTINGS = List.of(
            "ORACLE_TNS_ALIAS",
            "ORACLE_WALLET_RUTA",
            "ORACLE_USUARIO",
            "ORACLE_CONTRASENA");

    private final Environment environment;
    private final PagosProperties properties;

    public ProductionConfigurationValidator(Environment environment, PagosProperties properties) {
        this.environment = environment;
        this.properties = properties;
    }

    @Override
    public void run(ApplicationArguments args) {
        validate(System.getenv("SPRING_PROFILES_ACTIVE"), environment, properties);
    }

    public static void validate(
            String explicitlyActiveProfile,
            Environment environment,
            PagosProperties properties) {
        boolean productionProfileActive = Arrays.asList(environment.getActiveProfiles()).contains("produccion");
        if (productionProfileActive && !"produccion".equals(explicitlyActiveProfile)) {
            throw new IllegalStateException(
                    "La produccion requiere SPRING_PROFILES_ACTIVE=produccion configurado explicitamente.");
        }
        if (explicitlyActiveProfile == null || explicitlyActiveProfile.isBlank()) {
            return;
        }

        if (!"produccion".equals(explicitlyActiveProfile)
                && !"desarrollo".equals(explicitlyActiveProfile)) {
            throw new IllegalStateException(
                    "SPRING_PROFILES_ACTIVE debe ser exactamente desarrollo o produccion.");
        }
        if (!"produccion".equals(explicitlyActiveProfile)) {
            return;
        }

        for (String name : REQUIRED_ORACLE_SETTINGS) {
            requireConfigured(environment.getProperty(name), name);
        }
        String walletPath = environment.getProperty("ORACLE_WALLET_RUTA");
        if (!java.nio.file.Files.isDirectory(java.nio.file.Path.of(walletPath))) {
            throw new IllegalStateException("ORACLE_WALLET_RUTA debe apuntar a un directorio de wallet existente.");
        }

        requireHttps(environment.getProperty("JWT_JWKS_URL"), "JWT_JWKS_URL");
        requireHttps(environment.getProperty("JWT_EMISOR"), "JWT_EMISOR");
        requireConfigured(environment.getProperty("JWT_AUDIENCIA"), "JWT_AUDIENCIA");
        requireSecret(properties.getInternalSecret(), "INTERNO_SECRETO", DEVELOPMENT_INTERNAL_SECRET);
        requireSecret(properties.getQr().getSigningKey(), "COBRO_QR_CLAVE_FIRMA", DEVELOPMENT_QR_KEY);
        String topicArn = properties.getEvents().getSnsTopicArn();
        if (topicArn == null || !topicArn.startsWith("arn:aws:sns:")) {
            throw new IllegalStateException("SNS_TEMA_EVENTOS_ARN debe configurarse para produccion.");
        }
    }

    private static void requireHttps(String value, String name) {
        requireConfigured(value, name);
        URI uri;
        try {
            uri = URI.create(value);
        } catch (IllegalArgumentException ex) {
            throw new IllegalStateException(name + " debe ser una URL HTTPS valida.");
        }
        if (!"https".equalsIgnoreCase(uri.getScheme()) || uri.getHost() == null) {
            throw new IllegalStateException(name + " debe ser una URL HTTPS valida.");
        }
    }

    private static void requireConfigured(String value, String name) {
        if (value == null || value.isBlank()
                || value.toLowerCase(Locale.ROOT).contains("tu_")
                || value.toLowerCase(Locale.ROOT).contains("changeme")
                || value.toLowerCase(Locale.ROOT).contains("example")) {
            throw new IllegalStateException(name + " debe configurarse para produccion.");
        }
    }

    private static void requireSecret(String value, String name, String developmentValue) {
        if (value == null || value.length() < 32 || value.equals(developmentValue)
                || value.toLowerCase(Locale.ROOT).startsWith("dev-")) {
            throw new IllegalStateException(name + " debe ser un secreto de produccion de al menos 32 caracteres.");
        }
    }
}
