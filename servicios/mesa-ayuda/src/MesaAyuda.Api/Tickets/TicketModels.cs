using System.Text.Json.Serialization;
using MongoDB.Bson.Serialization.Attributes;

namespace MesaAyuda.Api.Tickets;

public sealed class SlaPolicyDocument
{
    [BsonId]
    [JsonPropertyName("prioridad")]
    public string Prioridad { get; set; } = "media";

    [JsonPropertyName("minutos_respuesta_n1")]
    public int MinutosRespuestaN1 { get; set; } = 30;

    [JsonPropertyName("minutos_resolucion")]
    public int MinutosResolucion { get; set; } = 240;
}

public sealed class TicketHistoryEntry
{
    [JsonPropertyName("fecha")]
    public DateTimeOffset Fecha { get; set; }

    [JsonPropertyName("actor_id")]
    public string ActorId { get; set; } = string.Empty;

    [JsonPropertyName("de_estado")]
    public string? DeEstado { get; set; }

    [JsonPropertyName("a_estado")]
    public string AEstado { get; set; } = string.Empty;

    [JsonPropertyName("nivel")]
    public string Nivel { get; set; } = "N1";

    [JsonPropertyName("nota")]
    public string? Nota { get; set; }
}

public sealed class TicketDocument
{
    [BsonId]
    [JsonPropertyName("id")]
    public string Id { get; set; } = Guid.NewGuid().ToString();

    [JsonPropertyName("numero")]
    public string Numero { get; set; } = string.Empty;

    [JsonPropertyName("evento_id")]
    public string? EventoId { get; set; }

    [JsonPropertyName("creado_por_id")]
    public string CreadoPorId { get; set; } = string.Empty;

    [JsonPropertyName("ubicacion")]
    public string Ubicacion { get; set; } = string.Empty;

    [JsonPropertyName("categoria")]
    public string Categoria { get; set; } = "otro";

    [JsonPropertyName("prioridad")]
    public string Prioridad { get; set; } = "media";

    [JsonPropertyName("nivel_actual")]
    public string NivelActual { get; set; } = "N1";

    [JsonPropertyName("estado")]
    public string Estado { get; set; } = "abierto";

    [JsonPropertyName("asignado_a_id")]
    public string? AsignadoAId { get; set; }

    [JsonPropertyName("descripcion")]
    public string Descripcion { get; set; } = string.Empty;

    [JsonPropertyName("sla_vence_en")]
    public DateTimeOffset SlaVenceEn { get; set; }

    [JsonPropertyName("sla_cumplido")]
    public bool? SlaCumplido { get; set; }

    [JsonPropertyName("sla_alerta_emitida")]
    public bool SlaAlertaEmitida { get; set; }

    [JsonPropertyName("historial")]
    public List<TicketHistoryEntry> Historial { get; set; } = new();

    [JsonPropertyName("creado_en")]
    public DateTimeOffset CreadoEn { get; set; } = DateTimeOffset.UtcNow;
}

public sealed record CreateTicketRequest(
    [property: JsonPropertyName("evento_id")] string? EventoId,
    [property: JsonPropertyName("ubicacion")] string Ubicacion,
    [property: JsonPropertyName("categoria")] string Categoria,
    [property: JsonPropertyName("prioridad")] string Prioridad,
    [property: JsonPropertyName("descripcion")] string Descripcion
);

public sealed record EscalateTicketRequest(
    [property: JsonPropertyName("nota")] string? Nota
);

public sealed record ResolveTicketRequest(
    [property: JsonPropertyName("nota")] string Nota
);
