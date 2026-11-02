# Modelo de datos de ExpoNexo

Cada servicio es dueño de su base. Este documento describe **qué guardar**, no cómo escribirlo:
tú traduces cada tabla a migraciones (Alembic en SQL Server, Flyway en Oracle) o a colecciones con
índices (MongoDB). Los tipos están en forma conceptual; al final de cada sección hay una guía de
cómo se llaman en ese motor.

**Convenciones para todas las tablas relacionales:**

- Llave primaria `id`. Investiga y decide entre entero autoincremental o UUID (anota la decisión
  en [DECISIONES.md](DECISIONES.md)). Sugerencia de estudio: «UUID vs identity primary key».
- `creado_en` y `actualizado_en` en **UTC**.
- Montos de dinero con decimales exactos (nunca punto flotante).
- Estados como texto corto con restricción de valores permitidos (investiga `CHECK constraint`).
- Toda llave foránea con índice.

---

## 1. Identidad, reservas y agenda (SQL Server)

### 1.1 `usuarios`

Cuentas de todas las personas.

| Columna | Tipo conceptual | Obligatoria | Descripción |
|---|---|---|---|
| id | identificador | sí | Llave primaria. |
| correo | texto (320) | sí | Único, guardado en minúsculas. |
| nombre | texto (120) | sí | Nombre para mostrar. |
| hash_contrasena | texto (255) | sí | Hash Argon2 (nunca la contraseña). |
| rol | texto corto | sí | `visitante`, `expositor`, `personal` o `administrador`. |
| empresa_id | identificador | no | Empresa a la que pertenece (expositores). Llave foránea a `empresas`. |
| activo | booleano | sí | Cuenta habilitada. |
| correo_verificado | booleano | sí | Confirmó su correo. |
| creado_en, actualizado_en | fecha y hora UTC | sí | Auditoría. |

Índices: único en `correo`.

### 1.2 `factores_mfa`

Métodos de verificación en dos pasos de cada cuenta (una fila por método).

| Columna | Tipo conceptual | Obligatoria | Descripción |
|---|---|---|---|
| id | identificador | sí | Llave primaria. |
| usuario_id | identificador | sí | Llave foránea a `usuarios`. |
| tipo | texto corto | sí | `app` o `correo`. |
| secreto_cifrado | texto | no | Clave de la app cifrada (solo tipo `app`). |
| activo | booleano | sí | Confirmado con su primer código. |
| preferido | booleano | sí | Es el que se pide por defecto. |
| ultimo_paso | entero grande | no | Último paso TOTP aceptado (impide reutilizar un código). |
| creado_en | fecha y hora UTC | sí | — |

Reglas: un solo método `preferido` por usuario; único por (`usuario_id`, `tipo`).

### 1.3 `codigos_verificacion`

Códigos de un solo uso enviados por correo (segundo paso, confirmación de correo, recuperación).

| Columna | Tipo conceptual | Descripción |
|---|---|---|
| id | identificador | Llave primaria. |
| usuario_id | identificador | Llave foránea. |
| proposito | texto corto | `ingreso`, `confirmar_correo`, `recuperar`, `activar_correo`. |
| huella | texto | Huella del código (nunca el código). |
| intentos | entero | Intentos fallidos. |
| vence_en | fecha y hora UTC | Vencimiento. |
| usado_en | fecha y hora UTC | Cuándo se usó (nulo si no). |

### 1.4 `codigos_respaldo`

| Columna | Tipo conceptual | Descripción |
|---|---|---|
| id | identificador | Llave primaria. |
| usuario_id | identificador | Llave foránea. |
| huella | texto | Huella del código de respaldo. |
| usado_en | fecha y hora UTC | Nulo hasta que se usa. |

### 1.5 `llaves_acceso`

Llaves WebAuthn (passkeys) registradas por cada usuario.

| Columna | Tipo conceptual | Descripción |
|---|---|---|
| id | identificador | Llave primaria. |
| usuario_id | identificador | Llave foránea. |
| credencial_id | texto o binario | Identificador de la credencial (único). |
| clave_publica | binario o texto | Clave pública de la credencial. |
| contador | entero grande | Contador de firmas (detecta clonación). |
| nombre_dispositivo | texto (60) | «Portátil», «Celular»… |
| creada_en, ultimo_uso_en | fecha y hora UTC | — |

### 1.6 `sesiones`

Tokens de refresco emitidos (para poder cerrar sesión y revocar).

| Columna | Tipo conceptual | Descripción |
|---|---|---|
| id | identificador | Llave primaria. |
| usuario_id | identificador | Llave foránea. |
| huella_token | texto | Huella del token de refresco. |
| creada_en, vence_en, revocada_en | fecha y hora UTC | Ciclo de vida. |
| agente | texto (200) | Navegador o aplicación (para mostrar «tus sesiones»). |

### 1.7 `intentos_ingreso`

Para limitar intentos y bloquear temporalmente.

| Columna | Tipo conceptual | Descripción |
|---|---|---|
| id | identificador | Llave primaria. |
| correo_huella | texto | Huella del correo intentado. |
| ip_huella | texto | Huella de la IP. |
| exito | booleano | Resultado. |
| ocurrido_en | fecha y hora UTC | Momento. |

Índices: (`correo_huella`, `ocurrido_en`) e (`ip_huella`, `ocurrido_en`).

### 1.8 `empresas`

| Columna | Tipo conceptual | Descripción |
|---|---|---|
| id | identificador | Llave primaria. |
| nit | texto (20) | Único. |
| razon_social | texto (150) | Nombre legal (va en la factura). |
| sector | texto (60) | Tecnología, alimentos, moda… |
| sitio_web | texto (200) | Opcional. |
| logo_url | texto (300) | Opcional. |

### 1.9 `eventos`

| Columna | Tipo conceptual | Descripción |
|---|---|---|
| id | identificador | Llave primaria. |
| nombre | texto (150) | «Feria de Tecnología 2027». |
| slug | texto (160) | Único, para la URL. |
| descripcion | texto largo | — |
| inicio, fin | fecha y hora UTC | Fechas del evento. |
| estado | texto corto | `borrador`, `publicado`, `en_curso`, `finalizado`, `cancelado`. |
| precio_entrada | decimal | Valor de la entrada general. |
| aforo | entero | Máximo de entradas. |

### 1.10 `pabellones`

| Columna | Tipo conceptual | Descripción |
|---|---|---|
| id | identificador | Llave primaria. |
| nombre | texto (60) | «Pabellón 3». |
| capacidad_stands | entero | — |
| plano_url | texto (300) | Imagen del plano (opcional). |

### 1.11 `stands`

| Columna | Tipo conceptual | Descripción |
|---|---|---|
| id | identificador | Llave primaria. |
| pabellon_id | identificador | Llave foránea. |
| codigo | texto (20) | «P3-A12». Único por pabellón. |
| metros_cuadrados | decimal | Área. |
| tipo | texto corto | `basico`, `esquinero`, `isla`. |
| precio_base | decimal | Precio por evento. |
| fila, columna | entero | Posición en la cuadrícula del plano del portal. |

### 1.12 `reservas_stand`

| Columna | Tipo conceptual | Descripción |
|---|---|---|
| id | identificador | Llave primaria. |
| evento_id | identificador | Llave foránea. |
| stand_id | identificador | Llave foránea. |
| empresa_id | identificador | Llave foránea. |
| usuario_id | identificador | Quién reservó. |
| estado | texto corto | `pendiente_pago`, `pagada`, `cancelada`, `vencida`. |
| monto | decimal | Precio congelado al reservar. |
| vence_en | fecha y hora UTC | Límite para pagar. |
| orden_pago_id | texto | Referencia a la orden en el servicio de pagos. |
| version | control de concurrencia | Investiga `rowversion` en SQL Server. |

Regla clave: **un stand no puede tener dos reservas activas en el mismo evento.** Investiga
«filtered unique index» para que la unicidad (`evento_id`, `stand_id`) aplique solo a los estados
`pendiente_pago` y `pagada`.

### 1.13 `entradas`

| Columna | Tipo conceptual | Descripción |
|---|---|---|
| id | identificador | Llave primaria. |
| evento_id | identificador | Llave foránea. |
| usuario_id | identificador | Visitante. |
| estado | texto corto | `pendiente_pago`, `activa`, `usada`, `cancelada`. |
| codigo_acceso_huella | texto | Huella del código del QR de ingreso. |
| precio | decimal | Congelado al comprar. |
| orden_pago_id | texto | Referencia a pagos. |
| usada_en | fecha y hora UTC | Ingreso al recinto. |

### 1.14 `salas`

| Columna | Tipo conceptual | Descripción |
|---|---|---|
| id | identificador | Llave primaria. |
| nombre | texto (60) | «Sala de negocios 2». |
| capacidad | entero | Personas. |

### 1.15 `disponibilidad`

Franjas en que un expositor acepta citas.

| Columna | Tipo conceptual | Descripción |
|---|---|---|
| id | identificador | Llave primaria. |
| usuario_id | identificador | Expositor. |
| evento_id | identificador | Evento. |
| inicio, fin | fecha y hora UTC | Franja. |

### 1.16 `citas`

| Columna | Tipo conceptual | Descripción |
|---|---|---|
| id | identificador | Llave primaria. |
| evento_id | identificador | Evento. |
| solicitante_id | identificador | Quien pide la cita. |
| invitado_id | identificador | Quien la recibe. |
| sala_id | identificador | Opcional (puede ser en el stand). |
| inicio, fin | fecha y hora UTC | Horario. |
| estado | texto corto | `propuesta`, `aceptada`, `rechazada`, `cancelada`. |
| mensaje | texto (500) | Motivo de la reunión. |

Regla: una persona no puede tener dos citas `aceptadas` que se solapen. Busca «overlapping
intervals condition».

### 1.17 `auditoria`

| Columna | Tipo conceptual | Descripción |
|---|---|---|
| id | identificador | Llave primaria. |
| usuario_id | identificador | Quién (nulo si fue el sistema). |
| accion | texto (40) | `reserva.creada`, `ingreso.fallido`… |
| entidad, entidad_id | texto | Sobre qué. |
| detalle | texto (400) | Sin datos sensibles. |
| correlacion_id | texto (64) | Para seguir la operación. |
| ocurrido_en | fecha y hora UTC | — |

### 1.18 `bandeja_salida` y `eventos_procesados`

Iguales en los tres servicios (ver [EVENTOS.md](EVENTOS.md)).

| `bandeja_salida` | Tipo conceptual | Descripción |
|---|---|---|
| id | identificador único global | Será el `id` del evento. |
| tipo | texto (60) | `reserva.creada`, `pago.aprobado`… |
| carga | texto JSON | Datos del evento. |
| correlacion_id | texto (64) | — |
| creado_en | fecha y hora UTC | — |
| publicado_en | fecha y hora UTC | Nulo hasta que se publica. |
| intentos | entero | Reintentos de publicación. |

| `eventos_procesados` | Tipo conceptual | Descripción |
|---|---|---|
| evento_id | identificador | Llave primaria: el `id` del evento recibido. |
| procesado_en | fecha y hora UTC | — |

**Guía SQL Server:** busca los tipos `NVARCHAR`, `DATETIME2`, `DECIMAL(12,2)`, `BIT`,
`UNIQUEIDENTIFIER`, `ROWVERSION` y cómo SQLAlchemy los representa
(«SQLAlchemy mssql dialect types»).

---

## 2. Pagos y facturación (Oracle)

### 2.1 `ordenes_pago`

| Columna | Tipo conceptual | Descripción |
|---|---|---|
| id | identificador | Llave primaria. |
| referencia | texto (64) | Id de la reserva o entrada en el otro servicio. |
| origen | texto corto | `stand` o `entrada`. |
| usuario_id | texto | Quien paga (el `sub` del token). |
| monto | decimal | — |
| moneda | texto (3) | `COP`. |
| estado | texto corto | `creada`, `pendiente`, `aprobada`, `rechazada`, `expirada`, `reembolsada`. |
| clave_idempotencia | texto (64) | Única: evita órdenes duplicadas por doble clic. |
| creada_en, actualizada_en | fecha y hora UTC | — |

### 2.2 `transacciones`

Cada intento de pago de una orden.

| Columna | Tipo conceptual | Descripción |
|---|---|---|
| id | identificador | Llave primaria. |
| orden_id | identificador | Llave foránea. |
| metodo | texto corto | `qr` (y luego otros). |
| estado | texto corto | `iniciada`, `aprobada`, `rechazada`. |
| codigo_autorizacion | texto (40) | Simulado. |
| ocurrida_en | fecha y hora UTC | — |

### 2.3 `cobros_qr`

| Columna | Tipo conceptual | Descripción |
|---|---|---|
| id | identificador | Llave primaria. |
| orden_id | identificador | Llave foránea. |
| contenido_huella | texto | Huella del contenido del QR. |
| vence_en | fecha y hora UTC | — |
| estado | texto corto | `vigente`, `pagado`, `vencido`. |

### 2.4 `facturas` y `detalle_factura`

| `facturas` | Tipo conceptual | Descripción |
|---|---|---|
| id | identificador | Llave primaria. |
| orden_id | identificador | Llave foránea (única). |
| numero | texto (20) | Prefijo + consecutivo («EXN-000123»). Único. |
| fecha | fecha y hora UTC | Emisión. |
| nit_cliente, razon_social | texto | Datos del comprador. |
| subtotal, impuesto, total | decimal | Valores. |
| estado | texto corto | `emitida`, `anulada`. |

| `detalle_factura` | Tipo conceptual | Descripción |
|---|---|---|
| id | identificador | Llave primaria. |
| factura_id | identificador | Llave foránea. |
| descripcion | texto (200) | «Stand P3-A12 · Feria de Tecnología». |
| cantidad | decimal | — |
| valor_unitario, impuesto | decimal | — |

### 2.5 `reembolsos`

| Columna | Tipo conceptual | Descripción |
|---|---|---|
| id | identificador | Llave primaria. |
| orden_id | identificador | Llave foránea. |
| monto | decimal | — |
| motivo | texto (200) | — |
| estado | texto corto | `solicitado`, `aprobado`, `rechazado`. |
| creado_en | fecha y hora UTC | — |

Más `bandeja_salida` y `eventos_procesados` (sección 1.18).

**Guía Oracle:** busca `VARCHAR2`, `NUMBER(12,2)`, `TIMESTAMP WITH TIME ZONE`, `RAW(16)` (UUID),
`GENERATED ALWAYS AS IDENTITY`, secuencias (`CREATE SEQUENCE`) para el consecutivo de facturas y
cómo se mapean con JPA («JPA Oracle identity column», «JPA BigDecimal precision scale»).

---

## 3. Mesa de ayuda y monitoreo (MongoDB)

En MongoDB no hay tablas sino **colecciones de documentos**. Se describen los campos de cada
documento y los índices que debes crear.

### 3.1 `tickets`

| Campo | Tipo | Descripción |
|---|---|---|
| `_id` | ObjectId | Identificador. |
| codigo | texto | «TCK-2027-00045». Único. |
| titulo, descripcion | texto | — |
| categoria | texto | `electricidad`, `red`, `limpieza`, `equipos`, `otro`. |
| prioridad | texto | `baja`, `media`, `alta`, `critica`. |
| estado | texto | `abierto`, `en_progreso`, `escalado`, `resuelto`, `cerrado`. |
| nivel | texto | `N1`, `N2`, `N3`. |
| solicitante | documento | { usuario_id, nombre, rol } |
| asignado | documento | { usuario_id, nombre } o nulo. |
| ubicacion | documento | { evento_id, pabellon, stand } |
| sla | documento | { horas_respuesta, horas_solucion, vence_en, cumplido } |
| historial | lista de documentos | { fecha, de_estado, a_estado, nota, por } |
| dispositivo_id | texto | Si lo abrió una alerta. |
| creado_en, actualizado_en | fecha | UTC. |

Índices: único en `codigo`; compuesto (`estado`, `prioridad`); `sla.vence_en`.

### 3.2 `politicas_sla`

| Campo | Tipo | Descripción |
|---|---|---|
| prioridad | texto | Única. |
| horas_respuesta | número | Tiempo para empezar a atender. |
| horas_solucion | número | Tiempo para resolver. |

### 3.3 `dispositivos`

| Campo | Tipo | Descripción |
|---|---|---|
| codigo | texto | «KIOSCO-P3-01». Único. |
| tipo | texto | `kiosco`, `pantalla`, `torniquete`. |
| ubicacion | documento | { pabellon, referencia } |
| estado | texto | `en_linea`, `sin_reporte`, `mantenimiento`. |
| ultimo_reporte | fecha | — |
| enrolado_en | fecha | — |

### 3.4 `lecturas` (colección time series)

| Campo | Tipo | Descripción |
|---|---|---|
| fecha | fecha | Campo de tiempo de la serie. |
| dispositivo | texto | Campo de metadatos (`metaField`). |
| cpu, memoria, disco | número | Porcentajes. |
| red_ok | booleano | — |

Índice **TTL**: las lecturas se borran solas a los 15 días (investiga `expireAfterSeconds` en
colecciones time series).

### 3.5 `alertas`

| Campo | Tipo | Descripción |
|---|---|---|
| dispositivo | texto | — |
| tipo | texto | `sin_reporte`, `cpu_alta`, `disco_lleno`. |
| inicio, fin | fecha | `fin` nulo mientras esté activa. |
| ticket_codigo | texto | Ticket que abrió. |

Más `bandeja_salida` y `eventos_procesados` como colecciones.

**Guía MongoDB:** busca «MongoDB data modeling embed vs reference», «MongoDB C# driver
CreateIndex», «MongoDB time series collection create», «MongoDB unique index».

---

## 4. Procedimientos almacenados (PA)

Las reglas que deben ser atómicas viven en la base, como en el resto del portafolio. Describe aquí
cada uno a medida que lo escribas (nombre, parámetros de entrada y salida, qué valida y qué
errores devuelve).

| Base | Procedimiento | Entradas | Salidas | Qué hace |
|---|---|---|---|---|
| SQL Server | `reservar_stand` | evento, stand, empresa, usuario, minutos de vencimiento, correlación | id de reserva, monto, vence_en | Valida que el stand esté libre y el evento publicado; crea la reserva `pendiente_pago`; escribe `reserva.creada` en la bandeja de salida. |
| SQL Server | `marcar_reserva_pagada` | reserva, orden de pago, id del evento recibido | — | Si el evento no fue procesado, pasa la reserva a `pagada`, guarda el evento en `eventos_procesados` y escribe `reserva.pagada`. |
| SQL Server | `vencer_reservas` | fecha de corte | cantidad vencida | Pasa a `vencida` las reservas no pagadas a tiempo y libera los stands. |
| SQL Server | `aceptar_cita` | cita, usuario | — | Verifica que no haya solapamiento con otras citas aceptadas y la acepta; escribe `cita.aceptada`. |
| Oracle (paquete `pkg_facturacion`) | `emitir_factura` | orden, datos del cliente | número de factura | Toma el consecutivo, crea la factura y su detalle, aprueba la orden y escribe `pago.aprobado`. |
| Oracle (paquete `pkg_facturacion`) | `registrar_reembolso` | orden, monto, motivo | id del reembolso | Valida el monto contra lo pagado y registra el reembolso; escribe `pago.reembolsado`. |

Busca: «stored procedure output parameters T-SQL», «PL/SQL OUT parameters», «stored procedures
vs application logic» (para justificar en [DECISIONES.md](DECISIONES.md) por qué estas reglas van
en la base).

## 5. Datos de prueba (semillas)

Para que el demo se vea vivo, prepara datos ficticios: 1 evento publicado, 3 pabellones,
40 stands, 8 empresas, un usuario de cada rol, 10 tickets y 6 dispositivos. Investiga cómo correr
semillas con cada herramienta («Alembic data migration», «Flyway repeatable migration»,
«MongoDB insertMany»). **Usa solo datos inventados**: nada de correos, NIT o personas reales.
