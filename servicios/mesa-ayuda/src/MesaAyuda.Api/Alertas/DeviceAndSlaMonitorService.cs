using System.Text.Json;
using MesaAyuda.Api.Bandeja;
using MesaAyuda.Api.Configuracion;
using MesaAyuda.Api.Datos;
using MesaAyuda.Api.Tickets;

namespace MesaAyuda.Api.Alertas;

public sealed class DeviceAndSlaMonitorService
{
    private readonly IMesaAyudaStore _store;
    private readonly MesaAyudaOptions _options;

    public DeviceAndSlaMonitorService(IMesaAyudaStore store, MesaAyudaOptions options)
    {
        _store = store;
        _options = options;
    }

    /// <summary>
    /// Detecta dispositivos que llevan más de DISPOSITIVO_SIN_REPORTE_MINUTOS sin reportar,
    /// los marca 'sin_reporte' y abre un único ticket automático de prioridad 'alta'
    /// (evitando crear duplicados en cada ciclo).
    /// También detecta tickets cuyo SLA venció sin estar resueltos ni cerrados.
    /// </summary>
    public async Task<(int OfflineDevicesDetected, int SlaBreachesDetected)> RunScanCycleAsync(
        DateTimeOffset? referenceNow = null,
        CancellationToken ct = default)
    {
        var now = referenceNow ?? DateTimeOffset.UtcNow;
        var cutoff = now.AddMinutes(-Math.Max(1, _options.DispositivoSinReporteMinutos));
        var policies = await _store.GetSlaPoliciesAsync(ct);

        int offlineCount = 0;
        var devices = await _store.ListDevicesAsync(ct);
        foreach (var dev in devices)
        {
            if (dev.Estado == "mantenimiento") continue;

            if (dev.UltimoReporteEn < cutoff && string.IsNullOrEmpty(dev.TicketAbiertoId))
            {
                var seq = await _store.GetNextTicketSequenceAsync(ct);
                var autoTicket = new TicketDocument
                {
                    Id = Guid.NewGuid().ToString(),
                    Numero = $"TCK-{seq:D4}",
                    CreadoPorId = "sistema-monitoreo",
                    Ubicacion = dev.Ubicacion,
                    Categoria = "dispositivo",
                    Prioridad = "alta",
                    NivelActual = "N1",
                    Estado = "abierto",
                    Descripcion = $"El dispositivo {dev.Codigo} ({dev.Tipo}) dejó de reportar desde {dev.UltimoReporteEn:O}.",
                    CreadoEn = now,
                    SlaVenceEn = SlaCalculator.CalculateDueAt(now, "alta", policies),
                    Historial = new List<TicketHistoryEntry>
                    {
                        new()
                        {
                            Fecha = now,
                            ActorId = "sistema-monitoreo",
                            DeEstado = null,
                            AEstado = "abierto",
                            Nivel = "N1",
                            Nota = $"Apertura automática por caída de dispositivo {dev.Codigo}"
                        }
                    }
                };

                var outboxEvent = new OutboxDocument
                {
                    Id = Guid.NewGuid().ToString(),
                    Tipo = "dispositivo.caido",
                    Carga = JsonSerializer.Serialize(new
                    {
                        dispositivo = dev.Codigo,
                        ubicacion = dev.Ubicacion,
                        ticket = autoTicket.Numero
                    }),
                    CorrelacionId = Guid.NewGuid().ToString(),
                    CreadoEn = now
                };

                await _store.CreateTicketAsync(autoTicket, outboxEvent, ct);

                dev.Estado = "sin_reporte";
                dev.TicketAbiertoId = autoTicket.Id;
                await _store.UpsertDeviceAsync(dev, ct);
                offlineCount++;
            }
        }

        int slaBreaches = 0;
        var activeTickets = await _store.ListTicketsAsync(null, null, null, null, ct);
        foreach (var ticket in activeTickets)
        {
            if (ticket.Estado is "resuelto" or "cerrado") continue;

            if (now > ticket.SlaVenceEn && !ticket.SlaAlertaEmitida)
            {
                ticket.SlaAlertaEmitida = true;
                ticket.SlaCumplido = false;
                var nextLevel = SlaCalculator.NextEscalationLevel(ticket.NivelActual);
                if (nextLevel is not null)
                {
                    var prev = ticket.Estado;
                    ticket.Estado = "escalado";
                    ticket.NivelActual = nextLevel;
                    ticket.Historial.Add(new TicketHistoryEntry
                    {
                        Fecha = now,
                        ActorId = "sistema-sla",
                        DeEstado = prev,
                        AEstado = "escalado",
                        Nivel = nextLevel,
                        Nota = "Escalamiento automático por vencimiento de SLA"
                    });
                }

                var outboxSla = new OutboxDocument
                {
                    Id = Guid.NewGuid().ToString(),
                    Tipo = "ticket.sla_vencido",
                    Carga = JsonSerializer.Serialize(new
                    {
                        ticket = ticket.Numero,
                        nivel = ticket.NivelActual,
                        usuario_id = ticket.CreadoPorId,
                        asignado_id = ticket.AsignadoAId
                    }),
                    CorrelacionId = Guid.NewGuid().ToString(),
                    CreadoEn = now
                };

                await _store.UpdateTicketAsync(ticket, outboxSla, ct);
                slaBreaches++;
            }
        }

        return (offlineCount, slaBreaches);
    }
}
