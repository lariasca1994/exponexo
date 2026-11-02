using MesaAyuda.Api.Bandeja;
using MesaAyuda.Api.Dispositivos;
using MesaAyuda.Api.Tickets;

namespace MesaAyuda.Api.Datos;

public interface IMesaAyudaStore
{
    Task<IReadOnlyList<SlaPolicyDocument>> GetSlaPoliciesAsync(CancellationToken ct = default);
    Task<TicketDocument> CreateTicketAsync(TicketDocument ticket, OutboxDocument? outboxEvent = null, CancellationToken ct = default);
    Task<TicketDocument?> GetTicketByIdAsync(string id, CancellationToken ct = default);
    Task<IReadOnlyList<TicketDocument>> ListTicketsAsync(
        string? creatorIdFilter,
        string? estadoFilter,
        string? prioridadFilter,
        string? nivelFilter,
        CancellationToken ct = default);
    Task UpdateTicketAsync(TicketDocument ticket, OutboxDocument? outboxEvent = null, CancellationToken ct = default);
    Task<int> GetNextTicketSequenceAsync(CancellationToken ct = default);

    Task<DeviceDocument?> GetDeviceByIdAsync(string id, CancellationToken ct = default);
    Task<DeviceDocument?> GetDeviceByCodeAsync(string codigo, CancellationToken ct = default);
    Task<DeviceDocument> UpsertDeviceAsync(DeviceDocument device, CancellationToken ct = default);
    Task<IReadOnlyList<DeviceDocument>> ListDevicesAsync(CancellationToken ct = default);
    Task AddDeviceReadingAsync(DeviceReadingDocument reading, CancellationToken ct = default);

    Task AddOutboxAsync(OutboxDocument outbox, CancellationToken ct = default);
    Task<IReadOnlyList<OutboxDocument>> ListPendingOutboxAsync(int maxBatch = 50, CancellationToken ct = default);
    Task MarkOutboxPublishedAsync(string id, DateTimeOffset publishedAt, CancellationToken ct = default);
}
