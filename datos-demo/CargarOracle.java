import java.nio.file.Files;
import java.nio.file.Path;
import java.sql.Connection;
import java.sql.DriverManager;
import java.sql.ResultSet;
import java.sql.Statement;
import java.util.Map;

/**
 * Ejecuta un script SQL en Oracle (una sentencia por bloque terminado en ';') y, con --verificar,
 * comprueba conteos y coherencia de los datos de pagos. Usa el mismo driver JDBC que el servicio.
 * Uso: java -cp "ojdbc11.jar:oraclepki.jar" CargarOracle.java <url-jdbc> <usuario> <archivo.sql> [--verificar]
 * La contraseña llega en la variable ORACLE_CONTRASENA (nunca como argumento).
 */
public class CargarOracle {
    public static void main(String[] args) throws Exception {
        String password = System.getenv("ORACLE_CONTRASENA");
        try (Connection c = DriverManager.getConnection(args[0], args[1], password); Statement s = c.createStatement()) {
            c.setAutoCommit(false);
            int ejecutadas = 0;
            for (String bloque : Files.readString(Path.of(args[2])).split(";\\s*(\\r?\\n|$)")) {
                String sql = bloque.lines().filter(l -> !l.trim().startsWith("--")).reduce("", (a, b) -> a + "\n" + b).trim();
                if (sql.isEmpty()) continue;
                if (sql.equalsIgnoreCase("COMMIT")) { c.commit(); continue; }
                s.execute(sql);
                ejecutadas++;
            }
            c.commit();
            System.out.println("Sentencias ejecutadas: " + ejecutadas);
            if (args.length > 3 && args[3].equals("--verificar")) {
                System.exit(verificar(s));
            }
        }
    }

    private static int verificar(Statement s) throws Exception {
        Map<String, String> consultas = Map.of(
            "ordenes de demostración (38)", "SELECT COUNT(*) FROM ordenes_pago WHERE clave_idempotencia LIKE 'demo-orden-%'",
            "facturas de demostración (33)", "SELECT COUNT(*) FROM facturas f JOIN ordenes_pago o ON o.id = f.orden_id WHERE o.clave_idempotencia LIKE 'demo-orden-%'",
            "aprobadas sin factura (0)", "SELECT COUNT(*) FROM ordenes_pago o WHERE o.estado = 'aprobada' AND NOT EXISTS (SELECT 1 FROM facturas f WHERE f.orden_id = o.id)",
            "facturas con total inconsistente (0)", "SELECT COUNT(*) FROM facturas WHERE total <> subtotal + impuesto",
            "facturas sin detalle (0)", "SELECT COUNT(*) FROM facturas f WHERE NOT EXISTS (SELECT 1 FROM detalle_factura d WHERE d.factura_id = f.id)");
        Map<String, Integer> esperado = Map.of(
            "ordenes de demostración (38)", 38, "facturas de demostración (33)", 33, "aprobadas sin factura (0)", 0,
            "facturas con total inconsistente (0)", 0, "facturas sin detalle (0)", 0);
        int fallas = 0;
        for (var entrada : consultas.entrySet()) {
            try (ResultSet r = s.executeQuery(entrada.getValue())) {
                r.next();
                int valor = r.getInt(1);
                boolean ok = valor == esperado.get(entrada.getKey());
                fallas += ok ? 0 : 1;
                System.out.println(entrada.getKey() + ": " + valor + (ok ? " ok" : " ERROR"));
            }
        }
        return fallas == 0 ? 0 : 1;
    }
}
