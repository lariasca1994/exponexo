using MesaAyuda.Api.Datos;
using MesaAyuda.Api.Dispositivos;
using MesaAyuda.Api.Tickets;
using MongoDB.Bson;
using Xunit;

public class MongoConventionsTests
{
    [Fact]
    public void DocumentsUseSnakeCaseFieldsAndBsonDates()
    {
        MongoConventions.Register();

        var reading = new DeviceReadingDocument { DispositivoId = "d-1", Momento = DateTimeOffset.UtcNow }.ToBsonDocument();
        Assert.True(reading.Contains("_id"));
        Assert.Equal(BsonType.DateTime, reading["momento"].BsonType);
        Assert.Equal("d-1", reading["dispositivo_id"].AsString);

        var ticket = new TicketDocument { Numero = "TCK-0001", Historial = { new TicketHistoryEntry() } }.ToBsonDocument();
        Assert.True(ticket.Contains("sla_vence_en") && ticket.Contains("creado_por_id"));
        Assert.Equal(BsonType.DateTime, ticket["historial"][0]["fecha"].BsonType);
    }
}
