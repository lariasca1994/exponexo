package co.exponexo.pagos.config;

import static org.junit.jupiter.api.Assertions.assertDoesNotThrow;
import static org.junit.jupiter.api.Assertions.assertThrows;

import java.nio.file.Files;
import org.junit.jupiter.api.Test;
import org.springframework.mock.env.MockEnvironment;

class ProductionConfigurationValidatorTests {

    @Test
    void productionRequiresExplicitProfileAndRealOracleJwtAndSecrets() throws Exception {
        var wallet = Files.createTempDirectory("oracle-wallet-test");
        var environment = new MockEnvironment()
                .withProperty("ORACLE_TNS_ALIAS", "exponexo_high")
                .withProperty("ORACLE_WALLET_RUTA", wallet.toString())
                .withProperty("ORACLE_USUARIO", "app_user")
                .withProperty("ORACLE_CONTRASENA", "test-password")
                .withProperty("JWT_JWKS_URL", "https://identity.exponexo.co/.well-known/jwks.json")
                .withProperty("JWT_EMISOR", "https://identity.exponexo.co")
                .withProperty("JWT_AUDIENCIA", "exponexo");
        var properties = new PagosProperties();
        properties.setInternalSecret("prod-internal-secret-value-123456789");
        properties.getQr().setSigningKey("prod-qr-signing-key-value-123456789");
        properties.getEvents().setSnsTopicArn("arn:aws:sns:us-east-1:000000000000:exponexo-eventos");

        assertDoesNotThrow(() ->
                ProductionConfigurationValidator.validate("produccion", environment, properties));
        assertDoesNotThrow(() ->
                ProductionConfigurationValidator.validate(null, environment, new PagosProperties()));

        properties.getEvents().setSnsTopicArn("");
        assertThrows(IllegalStateException.class, () ->
                ProductionConfigurationValidator.validate("produccion", environment, properties));
    }

    @Test
    void walletFromSecretIsExtractedAndPublishedAsWalletPath() throws Exception {
        var zip = new java.io.ByteArrayOutputStream();
        try (var out = new java.util.zip.ZipOutputStream(zip)) {
            out.putNextEntry(new java.util.zip.ZipEntry("tnsnames.ora"));
            out.write("exponexo_tp = (description=)".getBytes());
            out.putNextEntry(new java.util.zip.ZipEntry("../fuera.txt"));
            out.write("no".getBytes());
        }
        var environment = new MockEnvironment().withProperty(
                "ORACLE_WALLET_ZIP_BASE64", java.util.Base64.getEncoder().encodeToString(zip.toByteArray()));

        new OracleWalletEnvironmentPostProcessor().postProcessEnvironment(environment, null);

        var walletPath = java.nio.file.Path.of(environment.getProperty("ORACLE_WALLET_RUTA"));
        org.junit.jupiter.api.Assertions.assertTrue(Files.isRegularFile(walletPath.resolve("tnsnames.ora")));
        org.junit.jupiter.api.Assertions.assertFalse(Files.exists(walletPath.resolveSibling("fuera.txt")));
    }

    @Test
    void productionRejectsMissingDatabaseCredentialsOrHttpJwks() throws Exception {
        var wallet = Files.createTempDirectory("oracle-wallet-test");
        var environment = new MockEnvironment()
                .withProperty("ORACLE_TNS_ALIAS", "exponexo_high")
                .withProperty("ORACLE_WALLET_RUTA", wallet.toString())
                .withProperty("ORACLE_USUARIO", "app_user")
                .withProperty("ORACLE_CONTRASENA", "test-password")
                .withProperty("JWT_JWKS_URL", "http://identity.exponexo.co/.well-known/jwks.json")
                .withProperty("JWT_EMISOR", "https://identity.exponexo.co")
                .withProperty("JWT_AUDIENCIA", "exponexo");
        var properties = new PagosProperties();
        properties.setInternalSecret("prod-internal-secret-value-123456789");
        properties.getQr().setSigningKey("prod-qr-signing-key-value-123456789");

        assertThrows(IllegalStateException.class, () ->
                ProductionConfigurationValidator.validate("produccion", environment, properties));
        assertThrows(IllegalStateException.class, () ->
                ProductionConfigurationValidator.validate("production", environment, properties));
    }

    @Test
    void productionProfileCannotBeEnabledWithoutTheExplicitEnvironmentVariable() {
        var environment = new MockEnvironment();
        environment.setActiveProfiles("produccion");

        assertThrows(IllegalStateException.class, () ->
                ProductionConfigurationValidator.validate(null, environment, new PagosProperties()));
    }

    @Test
    void productionRejectsDevelopmentSecrets() throws Exception {
        var wallet = Files.createTempDirectory("oracle-wallet-test");
        var environment = new MockEnvironment()
                .withProperty("ORACLE_TNS_ALIAS", "exponexo_high")
                .withProperty("ORACLE_WALLET_RUTA", wallet.toString())
                .withProperty("ORACLE_USUARIO", "app_user")
                .withProperty("ORACLE_CONTRASENA", "test-password")
                .withProperty("JWT_JWKS_URL", "https://identity.exponexo.co/.well-known/jwks.json")
                .withProperty("JWT_EMISOR", "https://identity.exponexo.co")
                .withProperty("JWT_AUDIENCIA", "exponexo");
        var properties = new PagosProperties();
        properties.setInternalSecret("dev-interno-secreto");
        properties.getQr().setSigningKey("prod-qr-signing-key-value-123456789");

        assertThrows(IllegalStateException.class, () ->
                ProductionConfigurationValidator.validate("produccion", environment, properties));
    }
}
