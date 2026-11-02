# Registro de decisiones de arquitectura

Cada decisión importante se anota aquí en formato **ADR** (Architecture Decision Record): así,
dentro de seis meses (o en una entrevista) puedes explicar por qué está hecho así. Investiga
«Architecture Decision Records Michael Nygard».

**Formato de cada decisión:**

| Campo | Qué escribir |
|---|---|
| Número y título | «ADR-007: Procedimientos almacenados para reservas» |
| Estado | Propuesta, aceptada, reemplazada por ADR-XXX |
| Contexto | Qué problema había y qué restricciones |
| Opciones | Las alternativas que consideraste |
| Decisión | La que elegiste |
| Consecuencias | Qué ganas y qué pierdes |

---

## Decisiones ya tomadas (resúmelas con tus palabras en formato ADR)

| ADR | Decisión | Puntos para tu contexto y consecuencias |
|---|---|---|
| 001 | Monorepo con un servicio por carpeta | Un solo lugar para la documentación y los contratos; despliegue independiente por carpeta. |
| 002 | Cuatro servicios y una base por servicio | Separación por dominio de negocio; ningún servicio lee la base de otro. |
| 003 | FastAPI + SQL Server para identidad, reservas y agenda | Reglas transaccionales con cupos y fechas; muy común en empresas. |
| 004 | Spring Boot + Oracle para pagos y facturación | Estándar en banca y facturación; consecutivos y transacciones robustas. |
| 005 | ASP.NET Core + MongoDB para mesa de ayuda y monitoreo | Tickets con historial embebido y lecturas de dispositivos de alto volumen. |
| 006 | Cola de mensajes con bandeja de salida | Desacople y entrega confiable entre servicios. |
| 007 | Procedimientos almacenados para las reglas atómicas (reservas y facturación) | Consistencia garantizada por la base; igual que el resto del portafolio. |
| 008 | Identidad emite JWT RS256 y publica JWKS | Los demás servicios verifican sin conocer la clave privada. |
| 009 | Verificación en dos pasos obligatoria y llaves de acceso | Seguridad del ingreso a la altura de una plataforma real. |
| 010 | Portal React + TypeScript como PWA | Una interfaz para todos los roles, instalable. |
| 011 | Costo cero y escala a cero | Planes gratuitos; pantalla de espera mientras despiertan los servicios. |

## Decisiones que debes tomar tú (y anotar)

| ADR | Pregunta | Pistas para decidir |
|---|---|---|
| 012 | ¿Código y nombres en español o en inglés? | Coherencia con tu portafolio vs estándar internacional. |
| 013 | ¿Identificadores: entero autoincremental o UUID? | Seguridad (no adivinables), tamaño, rendimiento de índices. |
| 014 | ¿JSON en `camelCase` o `snake_case`? | Lo natural en JavaScript vs en Python. |
| 015 | ¿Dónde vive el token en el portal? | Memoria + refresco en cookie `HttpOnly` vs otras opciones (estudia los riesgos de cada una). |
| 016 | ¿Cómo se hablan el repartidor y los servicios: token de servicio o firma compartida? | Busca «service to service authentication patterns». |
