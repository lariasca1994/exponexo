using System.Collections.Concurrent;
using MesaAyuda.Api.Bandeja;
using MesaAyuda.Api.Dispositivos;
using MesaAyuda.Api.Tickets;

namespace MesaAyuda.Api.Datos;

public sealed class InMemoryMesaAyudaStore : IMesaAyudaStore
{
    private readonly ConcurrentDictionary<string, TicketDocument> _tickets = new();
    private readonly ConcurrentDictionary<string, DeviceDocument> _devices = new();
    private readonly ConcurrentBag<DeviceReadingDocument> _readings = new();
    private readonly ConcurrentDictionary<string, OutboxDocument> _outbox = new();
    private int _sequence;

    public Task<IReadOnlyList<SlaPolicyDocument>> GetSlaPoliciesAsync(CancellationToken ct = default) =>
        Task.FromResult<IReadOnlyList<SlaPolicyDocument>>(SlaCalculator.GetDefaultPolicies().ToList());

    public Task<int> GetNextTicketSequenceAsync(CancellationToken ct = default) =>
        Task.FromResult(Interlocked.Increment(ref _sequence));

    public Task<TicketDocument> CreateTicketAsync(
        TicketDocument ticket,
        OutboxDocument? outboxEvent = null,
        CancellationToken ct = default)
    {
        _tickets[ticket.Id] = ticket;
        if (outboxEvent is not null)
        {
            _outbox[outboxEvent.Id] = outboxEvent;
        }
        return Task.FromResult(ticket);
    }

    public Task<TicketDocument?> GetTicketByIdAsync(string id, CancellationToken ct = default)
    {
        _tickets.TryGetValue(id, out var found);
        return Task.FromResult(found);
    }

    public Task<IReadOnlyList<TicketDocument>> ListTicketsAsync(
        string? creatorIdFilter,
        string? estadoFilter,
        string? prioridadFilter,
        string? nivelFilter,
        CancellationToken ct = default)
    {
        IEnumerable<TicketDocument> query = _tickets.Values;

        if (!string.IsNullOrWhiteSpace(creatorIdFilter))
        {
            query = query.Where(t => string.Equals(t.CreadoPorId, creatorIdFilter, StringComparison.OrdinalIgnoreCase));
        }
        if (!string.IsNullOrWhiteSpace(estadoFilter))
        {
            query = query.Where(t => string.Equals(t.Estado, estadoFilter, StringComparison.OrdinalIgnoreCase));
        }
        if (!string.IsNullOrWhiteSpace(prioridadFilter))
        {
            query = query.Where(t => string.Equals(t.Prioridad, prioridadFilter, StringComparison.OrdinalIgnoreCase));
        }
        if (!string.IsNullOrWhiteSpace(nivelFilter))
        {
            query = query.Where(t => string.Equals(t.NivelActual, nivelFilter, StringComparison.OrdinalIgnoreCase));
        }

        var ordered = query.OrderByDescending(t => t.CreadoEn).ToList();
        return Task.FromResult<IReadOnlyList<TicketDocument>>(ordered);
    }

    public Task UpdateTicketAsync(
        TicketDocument ticket,
        OutboxDocument? outboxEvent = null,
        CancellationToken ct = default)
    {
        _tickets[ticket.Id] = ticket;
        if (outboxEvent is not null)
        {
            _outbox[outboxEvent.Id] = outboxEvent;
        }
        return Task.CompletedTask;
    }

    public Task<DeviceDocument?> GetDeviceByIdAsync(string id, CancellationToken ct = default)
    {
        _devices.TryGetValue(id, out var found);
        return Task.FromResult(found);
    }

    public Task<DeviceDocument?> GetDeviceByCodeAsync(string codigo, CancellationToken ct = default)
    {
        var found = _devices.Values.FirstOrDefault(d =>
            string.Equals(d.Codigo, codigo, StringComparison.OrdinalIgnoreCase));
        return Task.FromResult(found);
    }

    public Task<DeviceDocument> UpsertDeviceAsync(DeviceDocument device, CancellationToken ct = default)
    {
        _devices[device.Id] = device;
        return Task.FromResult(device);
    }

    public Task<IReadOnlyList<DeviceDocument>> ListDevicesAsync(CancellationToken ct = default)
    {
        var list = _devices.Values.OrderBy(d => d.Codigo).ToList();
        return Task.FromResult<IReadOnlyList<DeviceDocument>>(list);
    }

    public Task AddDeviceReadingAsync(DeviceReadingDocument reading, CancellationToken ct = default)
    {
        _readings.Add(reading);
        return Task.CompletedTask;
    }

    public Task AddOutboxAsync(OutboxDocument outbox, CancellationToken ct = default)
    {
        _outbox[outbox.Id] = outbox;
        return Task.CompletedTask;
    }

    public Task<IReadOnlyList<OutboxDocument>> ListPendingOutboxAsync(int maxBatch = 50, CancellationToken ct = default)
    {
        var list = _outbox.Values
            .Where(o => o.PublicadoEn is null)
            .OrderBy(o => o.CreadoEn)
            .Take(maxBatch)
            .ToList();
        return Task.FromResult<IReadOnlyList<OutboxDocument>>(list);
    }

    public Task MarkOutboxPublishedAsync(string id, DateTimeOffset publishedAt, CancellationToken ct = default)
    {
        if (_outbox.TryGetValue(id, out var doc))
        {
            doc.PublicadoEn = publishedAt;
            doc.Intentos += 1;
        }
        return Task.CompletedTask;
    }
}
