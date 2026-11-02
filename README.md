# ExpoNexo

**La plataforma que conecta un recinto de ferias con sus expositores y visitantes.**

ExpoNexo resuelve el día a día de un recinto de ferias y eventos: los expositores reservan y pagan
sus stands, los visitantes compran su entrada y agendan citas de negocios, y el personal del
recinto atiende incidentes y vigila los kioscos y pantallas durante el evento.

> Estado: **esqueleto**. El código se desarrolla por fases siguiendo
> [docs/MANUAL-DESARROLLO.md](docs/MANUAL-DESARROLLO.md).

## Qué hace (cuando esté terminado)

| Para quién | Qué puede hacer |
|---|---|
| **Expositor** | Ver el plano de pabellones, reservar un stand, pagarlo con QR, recibir su factura y agendar citas con visitantes. |
| **Visitante** | Comprar su entrada, ver expositores y pedir citas de negocios. |
| **Personal del recinto** | Abrir y atender tickets de soporte con SLA y ver el estado de kioscos y pantallas. |
| **Administrador** | Crear eventos, pabellones y stands, y ver ocupación, ingresos y asistencia. |

## Cómo está construido

Cuatro servicios, cada uno con su propia base de datos y una sola responsabilidad, más un portal
web que los une. Detalle en [docs/ARQUITECTURA.md](docs/ARQUITECTURA.md).

| Carpeta | Servicio | Tecnología | Base de datos |
|---|---|---|---|
| [portal/](portal/) | Portal web para todos los roles | React + TypeScript (Vite) | — |
| [servicios/identidad-reservas/](servicios/identidad-reservas/) | Cuentas, verificación en dos pasos, eventos, stands, entradas y citas | Python + FastAPI | SQL Server |
| [servicios/pagos/](servicios/pagos/) | Órdenes de pago, cobro con QR y facturación | Java + Spring Boot | Oracle |
| [servicios/mesa-ayuda/](servicios/mesa-ayuda/) | Tickets con SLA y monitoreo de dispositivos | C# + ASP.NET Core | MongoDB |
| [servicios/eventos/](servicios/eventos/) | Mensajes entre servicios y avisos por correo y Telegram | Python en funciones serverless | — (cola de mensajes) |

## Documentación

- [Manual de desarrollo](docs/MANUAL-DESARROLLO.md): por dónde empezar, fases, comandos y lista de chequeo.
- [Arquitectura](docs/ARQUITECTURA.md): cómo se comunican los servicios y por qué.
- [Modelo de datos](docs/MODELO-DE-DATOS.md): tablas y colecciones de cada servicio.
- [Contratos de API](docs/CONTRATOS-API.md): qué expone cada servicio.
- [Catálogo de eventos](docs/EVENTOS.md): qué mensajes viajan entre servicios.
- [Ruta de aprendizaje](docs/RUTA-DE-APRENDIZAJE.md): qué estudiar, en qué orden y qué buscar.
- [Diseño visual](docs/DISENO.md): cómo adaptar la plantilla que elijas.
- [Registro de decisiones](docs/DECISIONES.md): por qué se eligió cada tecnología.

## Autor

Proyecto de portafolio.
