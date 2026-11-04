package co.exponexo.pagos.config;

import java.io.ByteArrayInputStream;
import java.io.IOException;
import java.io.UncheckedIOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardCopyOption;
import java.util.Base64;
import java.util.Map;
import java.util.zip.ZipEntry;
import java.util.zip.ZipInputStream;
import org.springframework.boot.EnvironmentPostProcessor;
import org.springframework.boot.SpringApplication;
import org.springframework.core.env.ConfigurableEnvironment;
import org.springframework.core.env.MapPropertySource;

/**
 * En la nube el wallet de Oracle llega como secreto (ORACLE_WALLET_ZIP_BASE64) y no dentro de la
 * imagen: aquí se descomprime en un directorio temporal privado y se publica como ORACLE_WALLET_RUTA
 * antes de que se cree la conexión.
 */
public class OracleWalletEnvironmentPostProcessor implements EnvironmentPostProcessor {

    @Override
    public void postProcessEnvironment(ConfigurableEnvironment environment, SpringApplication application) {
        String encoded = environment.getProperty("ORACLE_WALLET_ZIP_BASE64");
        if (encoded == null || encoded.isBlank()) {
            return;
        }
        try {
            Path directory = Files.createTempDirectory("oracle-wallet");
            byte[] zip = Base64.getMimeDecoder().decode(encoded);
            try (ZipInputStream entries = new ZipInputStream(new ByteArrayInputStream(zip))) {
                for (ZipEntry entry; (entry = entries.getNextEntry()) != null; ) {
                    Path target = directory.resolve(entry.getName()).normalize();
                    if (entry.isDirectory() || !target.startsWith(directory)) {
                        continue;
                    }
                    Files.copy(entries, target, StandardCopyOption.REPLACE_EXISTING);
                }
            }
            environment.getPropertySources().addFirst(new MapPropertySource(
                    "oracleWallet", Map.of("ORACLE_WALLET_RUTA", directory.toString())));
        } catch (IOException ex) {
            throw new UncheckedIOException("No se pudo preparar el wallet de Oracle", ex);
        }
    }
}
