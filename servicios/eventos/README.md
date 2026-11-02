# Eventos entre servicios

**Cola de mensajes (Amazon SQS) · funciones serverless en Python (AWS Lambda) · AWS**

Lleva los mensajes de las bandejas de salida a quien los necesita y envía los avisos a las
personas. No tiene base de datos propia: su «estado» son las colas.

## Piezas

| Pieza | Qué hace |
|---|---|
| Cola `exponexo-eventos` | Recibe todos los eventos publicados por los servicios. |
| Cola `exponexo-eventos-errores` | Recibe los mensajes que fallaron varias veces (para revisarlos). |
| Función **repartidor** | Según el `tipo` del evento, llama a la ruta interna del servicio que debe reaccionar (por ejemplo, `pago.aprobado` → reservas marca la reserva pagada). |
| Función **avisos** | Envía correos con Brevo y mensajes de Telegram según el evento. |

Investiga si conviene **una cola por consumidor** (repartidor y avisos reciben cada uno su copia)
usando un tema SNS que reparte a varias colas: busca «SNS fan-out to SQS». Es el diseño más común
cuando dos consumidores necesitan el mismo evento; anota tu decisión en
[DECISIONES.md](../../docs/DECISIONES.md).

## Archivos que vas a crear (estructura sugerida)

```text
eventos/
├── repartidor/
│   ├── funcion.py        Punto de entrada de la Lambda: recorre el lote de mensajes de la cola,
│   │                     decide a qué servicio llamar y reporta los que fallaron.
│   ├── rutas.py          Tabla «tipo de evento → servicio y ruta interna».
│   └── requirements.txt
├── avisos/
│   ├── funcion.py        Punto de entrada: elige la plantilla según el tipo de evento.
│   ├── correo.py         Envío con la API de Brevo.
│   ├── telegram.py       Envío con la API de bots de Telegram.
│   ├── plantillas/       Textos de los correos (HTML y texto plano), sin datos sensibles.
│   └── requirements.txt
├── pruebas/              pytest con eventos de ejemplo (en JSON inventado).
├── .env.example          Plantilla de variables (ya está).
└── .env                  Tu copia con valores reales (no se sube).
```

## Qué estudiar antes

Bloque 4 de la [ruta de aprendizaje](../../docs/RUTA-DE-APRENDIZAJE.md) y el
[catálogo de eventos](../../docs/EVENTOS.md).

Puntos clave para investigar: «Lambda SQS partial batch response ReportBatchItemFailures» (que un
mensaje fallido no haga reintentar todo el lote), «SQS visibility timeout Lambda timeout», «Lambda
environment variables» y «Lambda function URL vs API Gateway» (no lo necesitas aquí, pero te lo
preguntarán en entrevistas).

## Comandos

| Para qué | Comando |
|---|---|
| Crear las colas | Ver la fase 4 del [manual](../../docs/MANUAL-DESARROLLO.md) |
| Ver mensajes en la cola (para depurar) | `aws sqs receive-message --queue-url URL_DE_LA_COLA --max-number-of-messages 5` |
| Ver cuántos mensajes hay | `aws sqs get-queue-attributes --queue-url URL_DE_LA_COLA --attribute-names ApproximateNumberOfMessages` |
| Empaquetar una función | `pip install -r requirements.txt -t paquete`, copia tus archivos a `paquete` y `Compress-Archive paquete\* funcion.zip` |
| Publicar el código | `aws lambda update-function-code --function-name exponexo-avisos --zip-file fileb://funcion.zip` |
| Ver logs | `aws logs tail /aws/lambda/exponexo-avisos --follow` |
| Pruebas locales | `pytest -q` |

## Lista de chequeo

- [ ] Un mensaje repetido no duplica efectos (idempotencia en el servicio que lo recibe).
- [ ] Un mensaje que falla 3 veces llega a la cola de errores.
- [ ] Los correos no contienen contraseñas, códigos ni datos de pago.
- [ ] Los logs se borran solos a los 14 días.
