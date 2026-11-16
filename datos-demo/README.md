# Datos de demostración

Datos ficticios y coherentes entre las tres bases, para mostrar el portal con contenido real:
3 eventos, 4 pabellones con 48 stands y 8 salas, 15 empresas expositoras, 40 personas, 25 reservas,
40 entradas, 20 citas de negocios, 38 órdenes de pago con 33 facturas, 30 tickets de soporte,
12 dispositivos y 200 lecturas recientes.

| Archivo | Para qué |
|---|---|
| `generar.py` | Única fuente: genera los tres scripts con identificadores deterministas |
| `identidad.sql` | Base de identidad y reservas |
| `pagos.sql` | Base de pagos: las facturas toman su número de la secuencia real |
| `mesa-ayuda.js` | Base de la mesa de ayuda |
| `cargar_sqlserver.py`, `CargarOracle.java` | Cargan y verifican conteos y coherencia |
| `imagenes.py` | Genera las portadas de los eventos, los logos de las empresas y los planos de los pabellones |

Reglas: todo es idempotente (correrlo de nuevo no duplica nada), los correos usan el dominio
`ejemplo.test` (no recibe correo), las personas ficticias no pueden iniciar sesión y no se tocan las
cuentas fijas ni las bandejas de eventos. 

## Cómo cargar

Desde GitHub: **Actions → Poblar datos de demostración → Run workflow**. Primero valida los tres
scripts en bases temporales y solo si todo pasa los carga en el entorno de la demo.

Para cambiar los datos, edita `generar.py`, corre `python datos-demo/generar.py` y sube los tres
archivos generados.
