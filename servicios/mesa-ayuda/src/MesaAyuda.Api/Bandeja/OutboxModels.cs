using System.Text.Json.Serialization;
using MongoDB.Bson.Serialization.Attributes;

namespace MesaAyuda.Api.Bandeja;

public sealed class OutboxDocument
{
    [BsonId]
    [JsonPropertyName("id")]
    public string Id { get; set; } = Guid.NewGuid().ToString();

    [JsonPropertyName("tipo")]
    public string Tipo { get; set; } = string.Empty;

    [JsonPropertyName("carga")]
    public string Carga { get; set; } = "{}";

    [JsonPropertyName("correlacion_id")]
    public string? CorrelacionId { get; set; }

    [JsonPropertyName("creado_en")]
    public DateTimeOffset CreadoEn { get; set; } = DateTimeOffset.UtcNow;

    [JsonPropertyName("publicado_en")]
    public DateTimeOffset? PublicadoEn { get; set; }

    [JsonPropertyName("intentos")]
    public int Intentos { get; set; }
}
