using MesaAyuda.Api.Bandeja;
using MesaAyuda.Api.Configuracion;
using MesaAyuda.Api.Dispositivos;
using MesaAyuda.Api.Tickets;
using MongoDB.Bson;
using MongoDB.Driver;

namespace MesaAyuda.Api.Datos;

public sealed class MongoMesaAyudaStore : IMesaAyudaStore
{
    private readonly IMongoDatabase _db;
    private readonly IMongoCollection<SlaPolicyDocument> _policies;
    private readonly IMongoCollection<TicketDocument> _tickets;
    private readonly IMongoCollection<DeviceDocument> _devices;
    private readonly IMongoCollection<DeviceReadingDocument> _readings;
    private readonly IMongoCollection<OutboxDocument> _outbox;
    private readonly int _retentionDays;
    private bool _initialized;

    public MongoMesaAyudaStore(MesaAyudaOptions options)
    {
        var client = new MongoClient(options.MongoUri);
        _db = client.GetDatabase(options.MongoBase);
        _policies = _db.GetCollection<SlaPolicyDocument>("politicas_sla");
        _tickets = _db.GetCollection<TicketDocument>("tickets");
        _devices = _db.GetCollection<DeviceDocument>("dispositivos");
        _readings = _db.GetCollection<DeviceReadingDocument>("lecturas_dispositivo");
        _outbox = _db.GetCollection<OutboxDocument>("bandeja_salida");
        _retentionDays = options.LecturaRetencionDias > 0 ? options.LecturaRetencionDias : 15;
    }

    private async Task EnsureIndexesAndPoliciesAsync(CancellationToken ct)
    {
        if (_initialized) return;

        // Colección time-series o índice TTL sobre lecturas_dispositivo.momento
        var existingCollections = await (await _db.ListCollectionNamesAsync(cancellationToken: ct)).ToListAsync(ct);
        if (!existingCollections.Contains("lecturas_dispositivo"))
        {
            var createOptions = new CreateCollectionOptions
            {
                TimeSeriesOptions = new TimeSeriesOptions(
                    timeField: "momento",
                    metaField: "dispositivo_id",
                    granularity: TimeSeriesGranularity.Seconds),
                ExpireAfter = TimeSpan.FromDays(_retentionDays)
            };
            await _db.CreateCollectionAsync("lecturas_dispositivo", createOptions, ct);
        }

        // Índices en tickets y dispositivos
        await _tickets.Indexes.CreateOneAsync(
            new CreateIndexModel<TicketDocument>(
                Builders<TicketDocument>.IndexKeys.Ascending(t => t.Numero),
                new CreateIndexOptions { Unique = true, Name = "uq_tickets_numero" }),
            cancellationToken: ct);

        await _devices.Indexes.CreateOneAsync(
            new CreateIndexModel<DeviceDocument>(
                Builders<DeviceDocument>.IndexKeys.Ascending(d => d.Codigo),
                new CreateIndexOptions { Unique = true, Name = "uq_dispositivos_codigo" }),
            cancellationToken: ct);

        // Sembrar políticas SLA por defecto si la colección está vacía
        var count = await _policies.CountDocumentsAsync(FilterDefinition<SlaPolicyDocument>.Empty, cancellationToken: ct);
        if (count == 0)
        {
            await _policies.InsertManyAsync(SlaCalculator.GetDefaultPolicies(), cancellationToken: ct);
        }

        _initialized = true;
    }

    public async Task<IReadOnlyList<SlaPolicyDocument>> GetSlaPoliciesAsync(CancellationToken ct = default)
    {
        await EnsureIndexesAndPoliciesAsync(ct);
        return await _policies.Find(FilterDefinition<SlaPolicyDocument>.Empty).ToListAsync(ct);
    }

    public async Task<int> GetNextTicketSequenceAsync(CancellationToken ct = default)
    {
        await EnsureIndexesAndPoliciesAsync(ct);
        var count = await _tickets.CountDocumentsAsync(FilterDefinition<TicketDocument>.Empty, cancellationToken: ct);
        return (int)count + 1;
    }

    public async Task<TicketDocument> CreateTicketAsync(
        TicketDocument ticket,
        OutboxDocument? outboxEvent = null,
        CancellationToken ct = default)
    {
        await EnsureIndexesAndPoliciesAsync(ct);
        await _tickets.InsertOneAsync(ticket, cancellationToken: ct);
        if (outboxEvent is not null)
        {
            await _outbox.InsertOneAsync(outboxEvent, cancellationToken: ct);
        }
        return ticket;
    }

    public async Task<TicketDocument?> GetTicketByIdAsync(string id, CancellationToken ct = default)
    {
        await EnsureIndexesAndPoliciesAsync(ct);
        return await _tickets.Find(t => t.Id == id).FirstOrDefaultAsync(ct);
    }

    public async Task<IReadOnlyList<TicketDocument>> ListTicketsAsync(
        string? creatorIdFilter,
        string? estadoFilter,
        string? prioridadFilter,
        string? nivelFilter,
        CancellationToken ct = default)
    {
        await EnsureIndexesAndPoliciesAsync(ct);
        var builder = Builders<TicketDocument>.Filter;
        var filter = builder.Empty;

        if (!string.IsNullOrWhiteSpace(creatorIdFilter))
        {
            filter &= builder.Eq(t => t.CreadoPorId, creatorIdFilter);
        }
        if (!string.IsNullOrWhiteSpace(estadoFilter))
        {
            filter &= builder.Eq(t => t.Estado, estadoFilter);
        }
        if (!string.IsNullOrWhiteSpace(prioridadFilter))
        {
            filter &= builder.Eq(t => t.Prioridad, prioridadFilter);
        }
        if (!string.IsNullOrWhiteSpace(nivelFilter))
        {
            filter &= builder.Eq(t => t.NivelActual, nivelFilter);
        }

        return await _tickets.Find(filter).SortByDescending(t => t.CreadoEn).ToListAsync(ct);
    }

    public async Task UpdateTicketAsync(
        TicketDocument ticket,
        OutboxDocument? outboxEvent = null,
        CancellationToken ct = default)
    {
        await EnsureIndexesAndPoliciesAsync(ct);
        await _tickets.ReplaceOneAsync(t => t.Id == ticket.Id, ticket, cancellationToken: ct);
        if (outboxEvent is not null)
        {
            await _outbox.InsertOneAsync(outboxEvent, cancellationToken: ct);
        }
    }

    public async Task<DeviceDocument?> GetDeviceByIdAsync(string id, CancellationToken ct = default)
    {
        await EnsureIndexesAndPoliciesAsync(ct);
        return await _devices.Find(d => d.Id == id).FirstOrDefaultAsync(ct);
    }

    public async Task<DeviceDocument?> GetDeviceByCodeAsync(string codigo, CancellationToken ct = default)
    {
        await EnsureIndexesAndPoliciesAsync(ct);
        return await _devices.Find(d => d.Codigo == codigo).FirstOrDefaultAsync(ct);
    }

    public async Task<DeviceDocument> UpsertDeviceAsync(DeviceDocument device, CancellationToken ct = default)
    {
        await EnsureIndexesAndPoliciesAsync(ct);
        await _devices.ReplaceOneAsync(
            d => d.Id == device.Id,
            device,
            new ReplaceOptions { IsUpsert = true },
            ct);
        return device;
    }

    public async Task<IReadOnlyList<DeviceDocument>> ListDevicesAsync(CancellationToken ct = default)
    {
        await EnsureIndexesAndPoliciesAsync(ct);
        return await _devices.Find(FilterDefinition<DeviceDocument>.Empty).SortBy(d => d.Codigo).ToListAsync(ct);
    }

    public async Task AddDeviceReadingAsync(DeviceReadingDocument reading, CancellationToken ct = default)
    {
        await EnsureIndexesAndPoliciesAsync(ct);
        await _readings.InsertOneAsync(reading, cancellationToken: ct);
    }

    public async Task AddOutboxAsync(OutboxDocument outbox, CancellationToken ct = default)
    {
        await EnsureIndexesAndPoliciesAsync(ct);
        await _outbox.InsertOneAsync(outbox, cancellationToken: ct);
    }

    public async Task<IReadOnlyList<OutboxDocument>> ListPendingOutboxAsync(int maxBatch = 50, CancellationToken ct = default)
    {
        await EnsureIndexesAndPoliciesAsync(ct);
        return await _outbox
            .Find(o => o.PublicadoEn == null)
            .SortBy(o => o.CreadoEn)
            .Limit(maxBatch)
            .ToListAsync(ct);
    }

    public async Task MarkOutboxPublishedAsync(string id, DateTimeOffset publishedAt, CancellationToken ct = default)
    {
        await EnsureIndexesAndPoliciesAsync(ct);
        var update = Builders<OutboxDocument>.Update
            .Set(o => o.PublicadoEn, publishedAt)
            .Inc(o => o.Intentos, 1);
        await _outbox.UpdateOneAsync(o => o.Id == id, update, cancellationToken: ct);
    }
}
