using System.Security.Cryptography;
using System.Text.Json;
using MesaAyuda.Api.Seguridad;
using MesaAyuda.Api.Alertas;
using MesaAyuda.Api.Bandeja;
using MesaAyuda.Api.Configuracion;
using MesaAyuda.Api.Datos;
using MesaAyuda.Api.Dispositivos;
using MesaAyuda.Api.Tickets;
using Microsoft.AspNetCore.Authentication.JwtBearer;
using Microsoft.IdentityModel.Tokens;

var builder = WebApplication.CreateBuilder(args);

var options = MesaAyudaOptions.FromConfiguration(builder.Configuration);
options.ValidateForEnvironment(builder.Environment.EnvironmentName);
builder.Services.AddSingleton(options);

var useInMemoryStore = MesaAyudaOptions.IsPlaceholderMongoUri(options.MongoUri);
if (useInMemoryStore
    && (builder.Environment.IsDevelopment() || builder.Environment.IsEnvironment("Testing")))
{
    builder.Services.AddSingleton<IMesaAyudaStore, InMemoryMesaAyudaStore>();
}
else if (useInMemoryStore)
{
    throw new InvalidOperationException("MONGO_URI debe configurarse; no se permite almacenamiento en memoria fuera de desarrollo/pruebas.");
}
else
{
    builder.Services.AddSingleton<IMesaAyudaStore, MongoMesaAyudaStore>();
}

builder.Services.AddSingleton<IJwksSigningKeyProvider>(
    _ => new JwksSigningKeyProvider(options.JwtJwksUrl));
builder.Services.AddAuthentication(JwtBearerDefaults.AuthenticationScheme)
    .AddJwtBearer();
builder.Services.AddOptions<JwtBearerOptions>(JwtBearerDefaults.AuthenticationScheme)
    .Configure<IJwksSigningKeyProvider>((jwt, keyProvider) =>
    {
        jwt.MapInboundClaims = false;
        jwt.TokenValidationParameters = new TokenValidationParameters
        {
            ValidateIssuer = true,
            ValidIssuer = options.JwtEmisor,
            ValidateAudience = true,
            ValidAudience = options.JwtAudiencia,
            ValidateLifetime = true,
            RequireExpirationTime = true,
            ValidateIssuerSigningKey = true,
            ValidAlgorithms = [SecurityAlgorithms.RsaSha256],
            NameClaimType = "sub",
            RoleClaimType = "rol",
            IssuerSigningKeyResolver = (_, _, keyId, _) => keyProvider.GetSigningKeys(keyId)
        };
        jwt.Events = new JwtBearerEvents
        {
            OnTokenValidated = context =>
            {
                var principal = context.Principal;
                if (string.IsNullOrWhiteSpace(principal?.FindFirst("sub")?.Value)
                    || string.IsNullOrWhiteSpace(principal.FindFirst("rol")?.Value)
                    || !string.Equals(
                        principal.FindFirst("token_use")?.Value,
                        "access",
                        StringComparison.Ordinal))
                {
                    context.Fail("JWT debe contener sub, rol y token_use=access.");
                }

                return Task.CompletedTask;
            }
        };
    });

builder.Services.AddSingleton<DeviceAndSlaMonitorService>();
if (!string.IsNullOrWhiteSpace(options.SnsTemaEventosArn))
{
    // Región y credenciales: AWS_REGION, AWS_ACCESS_KEY_ID y AWS_SECRET_ACCESS_KEY
    builder.Services.AddSingleton<Amazon.SimpleNotificationService.IAmazonSimpleNotificationService,
        Amazon.SimpleNotificationService.AmazonSimpleNotificationServiceClient>();
}
builder.Services.AddHostedService<OutboxPublisherService>();

var corsOrigins = (builder.Configuration["CORS_ORIGENES_PERMITIDOS"] ?? "http://localhost:5173")
    .Split(',', StringSplitOptions.RemoveEmptyEntries | StringSplitOptions.TrimEntries);

builder.Services.AddCors(cors =>
{
    cors.AddDefaultPolicy(policy =>
    {
        policy.WithOrigins(corsOrigins)
              .AllowAnyHeader()
              .AllowAnyMethod()
              .WithExposedHeaders("X-Correlation-Id", "X-Correlacion-Id");
    });
});

var app = builder.Build();

app.UseCors();

app.Use(async (ctx, next) =>
{
    var corrId = ctx.Request.Headers["X-Correlacion-Id"].FirstOrDefault()
                 ?? ctx.Request.Headers["X-Correlation-Id"].FirstOrDefault()
                 ?? Guid.NewGuid().ToString();
    ctx.Items["CorrelationId"] = corrId;
    ctx.Response.Headers["X-Correlacion-Id"] = corrId;
    ctx.Response.Headers["X-Correlation-Id"] = corrId;
    await next();
});
app.UseAuthentication();

static IResult ProblemResponse(HttpContext ctx, int status, string title, string detail, string typeSlug)
{
    var corrId = ctx.Items["CorrelationId"]?.ToString() ?? Guid.NewGuid().ToString();
    return Results.Json(
        new
        {
            type = $"https://exponexo.co/problemas/{typeSlug}",
            title,
            status,
            detail,
            instance = ctx.Request.Path.Value,
            correlacion_id = corrId
        },
        contentType: "application/problem+json",
        statusCode: status);
}

static (AuthenticatedPerson? Person, IResult? ErrorResult) RequireUser(
    HttpContext ctx,
    params string[] allowedRoles)
{
    if (ctx.User.Identity?.IsAuthenticated != true)
    {
        return (null, ProblemResponse(ctx, 401, "No autenticado", "Se requiere autenticacion Bearer.", "no-autenticado"));
    }

    var sub = ctx.User.FindFirst("sub")?.Value;
    var rol = ctx.User.FindFirst("rol")?.Value;
    var tokenUse = ctx.User.FindFirst("token_use")?.Value;
    if (string.IsNullOrWhiteSpace(sub) || string.IsNullOrWhiteSpace(rol))
    {
        return (null, ProblemResponse(ctx, 401, "Token incompleto", "El token no contiene sujeto o rol.", "token-incompleto"));
    }

    var person = new AuthenticatedPerson(sub, rol, tokenUse ?? string.Empty);
    if (allowedRoles.Length > 0 && !allowedRoles.Any(r => string.Equals(r, person.Rol, StringComparison.OrdinalIgnoreCase)))
    {
        return (null, ProblemResponse(ctx, 403, "Acceso denegado", "Tu rol no tiene permiso para realizar esta operaci?n.", "acceso-denegado"));
    }

    return (person, null);
}

app.MapGet("/salud", () => Results.Ok(new { estado = "ok", servicio = "mesa-ayuda" }));

// 1. Abrir un ticket
app.MapPost("/v1/tickets", async (
    HttpContext ctx,
    CreateTicketRequest req,
    IMesaAyudaStore store,
    CancellationToken ct) =>
{
    var (user, err) = RequireUser(ctx);
    if (err is not null) return err;

    var validCategories = new HashSet<string>(StringComparer.OrdinalIgnoreCase)
        { "red", "electrico", "mobiliario", "acceso", "dispositivo", "otro" };
    var validPriorities = new HashSet<string>(StringComparer.OrdinalIgnoreCase)
        { "baja", "media", "alta", "critica" };

    var categoria = string.IsNullOrWhiteSpace(req.Categoria) ? "otro" : req.Categoria.Trim().ToLowerInvariant();
    var prioridad = string.IsNullOrWhiteSpace(req.Prioridad) ? "media" : req.Prioridad.Trim().ToLowerInvariant();

    if (!validCategories.Contains(categoria))
    {
        return ProblemResponse(ctx, 400, "Categoría inválida", "La categoría del ticket no es válida.", "categoria-invalida");
    }
    if (!validPriorities.Contains(prioridad))
    {
        return ProblemResponse(ctx, 400, "Prioridad inválida", "La prioridad debe ser baja, media, alta o critica.", "prioridad-invalida");
    }
    if (string.IsNullOrWhiteSpace(req.Ubicacion) || string.IsNullOrWhiteSpace(req.Descripcion))
    {
        return ProblemResponse(ctx, 400, "Datos incompletos", "La ubicación y la descripción son obligatorias.", "datos-incompletos");
    }

    var now = DateTimeOffset.UtcNow;
    var policies = await store.GetSlaPoliciesAsync(ct);
    var seq = await store.GetNextTicketSequenceAsync(ct);
    var corrId = ctx.Items["CorrelationId"]?.ToString();

    var ticket = new TicketDocument
    {
        Id = Guid.NewGuid().ToString(),
        Numero = $"TCK-{seq:D4}",
        EventoId = req.EventoId,
        CreadoPorId = user!.Sub,
        Ubicacion = req.Ubicacion.Trim(),
        Categoria = categoria,
        Prioridad = prioridad,
        NivelActual = "N1",
        Estado = "abierto",
        Descripcion = req.Descripcion.Trim(),
        CreadoEn = now,
        SlaVenceEn = SlaCalculator.CalculateDueAt(now, prioridad, policies),
        Historial = new List<TicketHistoryEntry>
        {
            new()
            {
                Fecha = now,
                ActorId = user.Sub,
                DeEstado = null,
                AEstado = "abierto",
                Nivel = "N1",
                Nota = "Ticket creado"
            }
        }
    };

    var outbox = new OutboxDocument
    {
        Id = Guid.NewGuid().ToString(),
        Tipo = "ticket.creado",
        Carga = JsonSerializer.Serialize(new
        {
            ticket = ticket.Numero,
            prioridad = ticket.Prioridad,
            ubicacion = ticket.Ubicacion
        }),
        CorrelacionId = corrId,
        CreadoEn = now
    };

    await store.CreateTicketAsync(ticket, outbox, ct);
    return Results.Created($"/v1/tickets/{ticket.Id}", ticket);
});

// 2. Listar tickets
app.MapGet("/v1/tickets", async (
    HttpContext ctx,
    string? estado,
    string? prioridad,
    string? nivel,
    IMesaAyudaStore store,
    CancellationToken ct) =>
{
    var (user, err) = RequireUser(ctx);
    if (err is not null) return err;

    var isStaff = string.Equals(user!.Rol, "personal", StringComparison.OrdinalIgnoreCase)
                  || string.Equals(user.Rol, "administrador", StringComparison.OrdinalIgnoreCase);

    var creatorFilter = isStaff ? null : user.Sub;
    var list = await store.ListTicketsAsync(creatorFilter, estado, prioridad, nivel, ct);
    return Results.Ok(list);
});

// 3. Detalle de ticket con historial
app.MapGet("/v1/tickets/{id}", async (
    string id,
    HttpContext ctx,
    IMesaAyudaStore store,
    CancellationToken ct) =>
{
    var (user, err) = RequireUser(ctx);
    if (err is not null) return err;

    var ticket = await store.GetTicketByIdAsync(id, ct);
    if (ticket is null)
    {
        return ProblemResponse(ctx, 404, "Ticket no encontrado", "No existe el ticket solicitado.", "ticket-no-encontrado");
    }

    var isStaff = string.Equals(user!.Rol, "personal", StringComparison.OrdinalIgnoreCase)
                  || string.Equals(user.Rol, "administrador", StringComparison.OrdinalIgnoreCase);

    if (!isStaff && !string.Equals(ticket.CreadoPorId, user.Sub, StringComparison.OrdinalIgnoreCase))
    {
        return ProblemResponse(ctx, 403, "Acceso denegado", "Solo quien creó el ticket o el personal puede consultarlo.", "ticket-ajeno");
    }

    return Results.Ok(ticket);
});

// 4. Tomar el ticket
app.MapPost("/v1/tickets/{id}/tomar", async (
    string id,
    HttpContext ctx,
    IMesaAyudaStore store,
    CancellationToken ct) =>
{
    var (user, err) = RequireUser(ctx, "personal", "administrador");
    if (err is not null) return err;

    var ticket = await store.GetTicketByIdAsync(id, ct);
    if (ticket is null)
    {
        return ProblemResponse(ctx, 404, "Ticket no encontrado", "No existe el ticket solicitado.", "ticket-no-encontrado");
    }

    if (ticket.Estado is "resuelto" or "cerrado")
    {
        return ProblemResponse(ctx, 409, "Ticket finalizado", "No se puede tomar un ticket que ya fue resuelto o cerrado.", "ticket-finalizado");
    }

    var previous = ticket.Estado;
    ticket.Estado = "en_atencion";
    ticket.AsignadoAId = user!.Sub;
    ticket.Historial.Add(new TicketHistoryEntry
    {
        Fecha = DateTimeOffset.UtcNow,
        ActorId = user.Sub,
        DeEstado = previous,
        AEstado = "en_atencion",
        Nivel = ticket.NivelActual,
        Nota = "Ticket tomado para atención"
    });

    await store.UpdateTicketAsync(ticket, null, ct);
    return Results.Ok(ticket);
});

// 5. Escalar el ticket (N1 -> N2 -> N3)
app.MapPost("/v1/tickets/{id}/escalar", async (
    string id,
    EscalateTicketRequest? req,
    HttpContext ctx,
    IMesaAyudaStore store,
    CancellationToken ct) =>
{
    var (user, err) = RequireUser(ctx, "personal", "administrador");
    if (err is not null) return err;

    var ticket = await store.GetTicketByIdAsync(id, ct);
    if (ticket is null)
    {
        return ProblemResponse(ctx, 404, "Ticket no encontrado", "No existe el ticket solicitado.", "ticket-no-encontrado");
    }

    if (ticket.Estado is "resuelto" or "cerrado")
    {
        return ProblemResponse(ctx, 409, "Ticket finalizado", "No se puede escalar un ticket resuelto o cerrado.", "ticket-finalizado");
    }

    var nextLevel = SlaCalculator.NextEscalationLevel(ticket.NivelActual);
    if (nextLevel is null)
    {
        return ProblemResponse(ctx, 409, "Nivel máximo alcanzado", "El ticket ya se encuentra en el nivel máximo (N3).", "ticket-nivel-maximo");
    }

    var previous = ticket.Estado;
    ticket.Estado = "escalado";
    ticket.NivelActual = nextLevel;
    ticket.Historial.Add(new TicketHistoryEntry
    {
        Fecha = DateTimeOffset.UtcNow,
        ActorId = user!.Sub,
        DeEstado = previous,
        AEstado = "escalado",
        Nivel = nextLevel,
        Nota = string.IsNullOrWhiteSpace(req?.Nota) ? $"Escalado a {nextLevel}" : req!.Nota
    });

    await store.UpdateTicketAsync(ticket, null, ct);
    return Results.Ok(ticket);
});

// 6. Resolver el ticket con nota
app.MapPost("/v1/tickets/{id}/resolver", async (
    string id,
    ResolveTicketRequest req,
    HttpContext ctx,
    IMesaAyudaStore store,
    CancellationToken ct) =>
{
    var (user, err) = RequireUser(ctx, "personal", "administrador");
    if (err is not null) return err;

    var ticket = await store.GetTicketByIdAsync(id, ct);
    if (ticket is null)
    {
        return ProblemResponse(ctx, 404, "Ticket no encontrado", "No existe el ticket solicitado.", "ticket-no-encontrado");
    }

    if (ticket.Estado is "resuelto" or "cerrado")
    {
        return ProblemResponse(ctx, 409, "Ticket ya resuelto", "El ticket ya fue marcado como resuelto anteriormente.", "ticket-ya-resuelto");
    }

    var now = DateTimeOffset.UtcNow;
    var previous = ticket.Estado;
    ticket.Estado = "resuelto";
    ticket.AsignadoAId ??= user!.Sub;
    ticket.SlaCumplido = now <= ticket.SlaVenceEn;
    ticket.Historial.Add(new TicketHistoryEntry
    {
        Fecha = now,
        ActorId = user!.Sub,
        DeEstado = previous,
        AEstado = "resuelto",
        Nivel = ticket.NivelActual,
        Nota = string.IsNullOrWhiteSpace(req.Nota) ? "Ticket resuelto" : req.Nota.Trim()
    });

    await store.UpdateTicketAsync(ticket, null, ct);
    return Results.Ok(ticket);
});

// 7. Enrolar un dispositivo del recinto (kiosco, pantalla o torniquete)
app.MapPost("/v1/dispositivos/enrolar", async (
    EnrollDeviceRequest req,
    HttpContext ctx,
    MesaAyudaOptions opts,
    IMesaAyudaStore store,
    CancellationToken ct) =>
{
    if (string.IsNullOrWhiteSpace(req.CodigoEnrolamiento)
        || !string.Equals(req.CodigoEnrolamiento.Trim(), opts.DispositivoCodigoEnrolamiento, StringComparison.Ordinal))
    {
        return ProblemResponse(ctx, 401, "Código de enrolamiento inválido", "El código de enrolamiento del recinto no es válido.", "enrolamiento-invalido");
    }

    var validTypes = new HashSet<string>(StringComparer.OrdinalIgnoreCase)
        { "kiosco", "pantalla", "torniquete" };
    var tipo = (req.Tipo ?? "kiosco").Trim().ToLowerInvariant();
    if (!validTypes.Contains(tipo))
    {
        return ProblemResponse(ctx, 400, "Tipo de dispositivo inválido", "El tipo debe ser kiosco, pantalla o torniquete.", "tipo-dispositivo-invalido");
    }

    var rawTokenBytes = RandomNumberGenerator.GetBytes(32);
    var deviceToken = Convert.ToBase64String(rawTokenBytes)
        .Replace('+', '-')
        .Replace('/', '_')
        .TrimEnd('=');

    var existing = await store.GetDeviceByCodeAsync(req.Codigo.Trim(), ct);
    var device = existing ?? new DeviceDocument
    {
        Id = Guid.NewGuid().ToString(),
        Codigo = req.Codigo.Trim()
    };

    device.Tipo = tipo;
    device.Ubicacion = req.Ubicacion.Trim();
    device.VersionFirmware = string.IsNullOrWhiteSpace(req.VersionFirmware) ? "1.0.0" : req.VersionFirmware.Trim();
    device.SecretoHash = DeviceTokenHasher.HashSecret(deviceToken);
    device.Estado = "en_linea";
    device.UltimoReporteEn = DateTimeOffset.UtcNow;
    device.TicketAbiertoId = null;

    await store.UpsertDeviceAsync(device, ct);

    return Results.Created(
        $"/v1/dispositivos/{device.Id}",
        new EnrollDeviceResponse(device.Id, device.Codigo, deviceToken, device.Estado));
});

// 8. Recibir lectura periódica de un dispositivo (autenticado con su propio secreto, no JWT de persona)
app.MapPost("/v1/dispositivos/{id}/lecturas", async (
    string id,
    DeviceReadingRequest req,
    HttpContext ctx,
    IMesaAyudaStore store,
    CancellationToken ct) =>
{
    var deviceToken = ctx.Request.Headers["X-Token-Dispositivo"].FirstOrDefault();
    if (string.IsNullOrWhiteSpace(deviceToken))
    {
        return ProblemResponse(ctx, 401, "Credencial de dispositivo requerida", "Los dispositivos deben autenticarse con el encabezado X-Token-Dispositivo.", "dispositivo-no-autenticado");
    }

    var device = await store.GetDeviceByIdAsync(id, ct);
    if (device is null)
    {
        return ProblemResponse(ctx, 404, "Dispositivo no encontrado", "El dispositivo indicado no está registrado.", "dispositivo-no-encontrado");
    }

    if (!DeviceTokenHasher.VerifySecret(deviceToken.Trim(), device.SecretoHash))
    {
        return ProblemResponse(ctx, 401, "Token de dispositivo inválido", "La credencial del dispositivo no coincide.", "dispositivo-credencial-invalida");
    }

    var now = DateTimeOffset.UtcNow;
    device.UltimoReporteEn = now;
    device.Estado = "en_linea";
    device.TicketAbiertoId = null;
    await store.UpsertDeviceAsync(device, ct);

    var reading = new DeviceReadingDocument
    {
        Id = Guid.NewGuid().ToString(),
        DispositivoId = device.Id,
        Momento = now,
        CpuPorcentaje = req.CpuPorcentaje,
        MemoriaPorcentaje = req.MemoriaPorcentaje,
        TemperaturaC = req.TemperaturaC,
        Conectado = req.Conectado
    };
    await store.AddDeviceReadingAsync(reading, ct);

    return Results.Accepted($"/v1/dispositivos/{device.Id}", new { recibido = true, momento = now });
});

// 9. Listar dispositivos del recinto
app.MapGet("/v1/dispositivos", async (
    HttpContext ctx,
    IMesaAyudaStore store,
    CancellationToken ct) =>
{
    var (_, err) = RequireUser(ctx, "personal", "administrador");
    if (err is not null) return err;

    var devices = await store.ListDevicesAsync(ct);
    return Results.Ok(devices);
});

// 10. Ruta interna para ejecutar barrido de monitoreo (dispositivos sin reporte y vencimientos SLA)
app.MapPost("/v1/interno/monitoreo/ejecutar", async (
    HttpContext ctx,
    DeviceAndSlaMonitorService monitor,
    CancellationToken ct) =>
{
    var (svc, err) = RequireUser(ctx, "interno", "administrador");
    if (err is not null) return err;

    var (offline, slaBreaches) = await monitor.RunScanCycleAsync(null, ct);
    return Results.Ok(new
    {
        dispositivos_caidos_detectados = offline,
        sla_vencidos_detectados = slaBreaches,
        ejecutado_por = svc!.Sub
    });
});

// 11. Resumen para el tablero del administrador (Fase 7)
app.MapGet("/v1/admin/resumen", async (
    HttpContext ctx,
    IMesaAyudaStore store,
    CancellationToken ct) =>
{
    var (_, err) = RequireUser(ctx, "administrador");
    if (err is not null) return err;

    var tickets = await store.ListTicketsAsync(null, null, null, null, ct);
    var devices = await store.ListDevicesAsync(ct);

    var resolved = tickets.Where(t => t.SlaCumplido.HasValue).ToList();
    var slaMet = resolved.Count(t => t.SlaCumplido == true);
    var slaPercent = resolved.Count > 0
        ? Math.Round((double)slaMet * 100.0 / resolved.Count, 2)
        : 100.0;

    return Results.Ok(new
    {
        tickets_totales = tickets.Count,
        tickets_abiertos = tickets.Count(t => t.Estado is "abierto" or "en_atencion" or "escalado"),
        tickets_resueltos = tickets.Count(t => t.Estado is "resuelto" or "cerrado"),
        por_prioridad = new
        {
            baja = tickets.Count(t => t.Prioridad == "baja"),
            media = tickets.Count(t => t.Prioridad == "media"),
            alta = tickets.Count(t => t.Prioridad == "alta"),
            critica = tickets.Count(t => t.Prioridad == "critica")
        },
        cumplimiento_sla_porcentaje = slaPercent,
        dispositivos_totales = devices.Count,
        dispositivos_en_linea = devices.Count(d => d.Estado == "en_linea"),
        dispositivos_sin_reporte = devices.Count(d => d.Estado == "sin_reporte")
    });
});

app.Run();

public sealed record AuthenticatedPerson(string Sub, string Rol, string TokenUse);

public partial class Program { }
