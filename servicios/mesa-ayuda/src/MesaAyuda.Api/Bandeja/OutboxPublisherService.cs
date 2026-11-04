using System.Text.Json;
using System.Text.Json.Nodes;
using Amazon.SimpleNotificationService;
using Amazon.SimpleNotificationService.Model;
using MesaAyuda.Api.Configuracion;
using MesaAyuda.Api.Datos;

namespace MesaAyuda.Api.Bandeja;

/// <summary>
/// Publica la bandeja de salida en el tema SNS de eventos cada pocos segundos mientras el
/// contenedor esté despierto. Sin tema configurado (desarrollo) solo registra el evento.
/// </summary>
public sealed class OutboxPublisherService(
    IMesaAyudaStore store,
    MesaAyudaOptions options,
    ILogger<OutboxPublisherService> logger,
    IAmazonSimpleNotificationService? sns = null) : BackgroundService
{
    private static readonly TimeSpan Interval = TimeSpan.FromSeconds(15);

    protected override async Task ExecuteAsync(CancellationToken stoppingToken)
    {
        using var timer = new PeriodicTimer(Interval);
        do
        {
            try
            {
                await PublishPendingAsync(stoppingToken);
            }
            catch (Exception ex) when (ex is not OperationCanceledException)
            {
                logger.LogError(ex, "Ciclo de publicación de la bandeja falló");
            }
        } while (await timer.WaitForNextTickAsync(stoppingToken));
    }

    public async Task<int> PublishPendingAsync(CancellationToken ct = default)
    {
        var published = 0;
        foreach (var message in await store.ListPendingOutboxAsync(50, ct))
        {
            try
            {
                var envelope = new JsonObject
                {
                    ["id"] = message.Id,
                    ["tipo"] = message.Tipo,
                    ["version"] = 1,
                    ["ocurrido_en"] = message.CreadoEn.ToUniversalTime().ToString("O"),
                    ["origen"] = "mesa-ayuda",
                    ["correlacion_id"] = message.CorrelacionId,
                    ["datos"] = JsonNode.Parse(message.Carga),
                };

                if (sns is null || string.IsNullOrWhiteSpace(options.SnsTemaEventosArn))
                {
                    logger.LogInformation("Outbox local simulado [{Tipo}]: {Id}", message.Tipo, message.Id);
                }
                else
                {
                    await sns.PublishAsync(new PublishRequest
                    {
                        TopicArn = options.SnsTemaEventosArn,
                        Message = envelope.ToJsonString(),
                        MessageAttributes = new Dictionary<string, MessageAttributeValue>
                        {
                            ["tipo"] = new() { DataType = "String", StringValue = message.Tipo },
                        },
                    }, ct);
                }

                await store.MarkOutboxPublishedAsync(message.Id, DateTimeOffset.UtcNow, ct);
                published++;
            }
            catch (Exception ex) when (ex is AmazonSimpleNotificationServiceException or JsonException or HttpRequestException)
            {
                logger.LogError("Fallo al publicar el mensaje de bandeja {Id}: {Error}", message.Id, ex.Message);
            }
        }
        return published;
    }
}
