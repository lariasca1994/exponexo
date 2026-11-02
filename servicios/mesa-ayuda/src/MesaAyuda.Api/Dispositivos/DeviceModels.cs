using System.Security.Cryptography;
using System.Text;
using System.Text.Json.Serialization;
using MongoDB.Bson.Serialization.Attributes;

namespace MesaAyuda.Api.Dispositivos;

public sealed class DeviceDocument
{
    [BsonId]
    [JsonPropertyName("id")]
    public string Id { get; set; } = Guid.NewGuid().ToString();

    [JsonPropertyName("codigo")]
    public string Codigo { get; set; } = string.Empty;

    [JsonPropertyName("tipo")]
    public string Tipo { get; set; } = "kiosco";

    [JsonPropertyName("ubicacion")]
    public string Ubicacion { get; set; } = string.Empty;

    [JsonIgnore]
    public string SecretoHash { get; set; } = string.Empty;

    [JsonPropertyName("estado")]
    public string Estado { get; set; } = "en_linea";

    [JsonPropertyName("ultimo_reporte_en")]
    public DateTimeOffset UltimoReporteEn { get; set; } = DateTimeOffset.UtcNow;

    [JsonPropertyName("version_firmware")]
    public string VersionFirmware { get; set; } = "1.0.0";

    [JsonPropertyName("ticket_abierto_id")]
    public string? TicketAbiertoId { get; set; }
}

public sealed class DeviceReadingDocument
{
    [BsonId]
    [JsonPropertyName("id")]
    public string Id { get; set; } = Guid.NewGuid().ToString();

    [JsonPropertyName("dispositivo_id")]
    public string DispositivoId { get; set; } = string.Empty;

    [JsonPropertyName("momento")]
    public DateTimeOffset Momento { get; set; } = DateTimeOffset.UtcNow;

    [JsonPropertyName("cpu_porcentaje")]
    public double CpuPorcentaje { get; set; }

    [JsonPropertyName("memoria_porcentaje")]
    public double MemoriaPorcentaje { get; set; }

    [JsonPropertyName("temperatura_c")]
    public double TemperaturaC { get; set; }

    [JsonPropertyName("conectado")]
    public bool Conectado { get; set; } = true;
}

public sealed record EnrollDeviceRequest(
    [property: JsonPropertyName("codigo_enrolamiento")] string CodigoEnrolamiento,
    [property: JsonPropertyName("codigo")] string Codigo,
    [property: JsonPropertyName("tipo")] string Tipo,
    [property: JsonPropertyName("ubicacion")] string Ubicacion,
    [property: JsonPropertyName("version_firmware")] string? VersionFirmware
);

public sealed record EnrollDeviceResponse(
    [property: JsonPropertyName("dispositivo_id")] string DispositivoId,
    [property: JsonPropertyName("codigo")] string Codigo,
    [property: JsonPropertyName("token_dispositivo")] string TokenDispositivo,
    [property: JsonPropertyName("estado")] string Estado
);

public sealed record DeviceReadingRequest(
    [property: JsonPropertyName("cpu_porcentaje")] double CpuPorcentaje,
    [property: JsonPropertyName("memoria_porcentaje")] double MemoriaPorcentaje,
    [property: JsonPropertyName("temperatura_c")] double TemperaturaC,
    [property: JsonPropertyName("conectado")] bool Conectado = true
);

public static class DeviceTokenHasher
{
    public static string HashSecret(string rawSecret)
    {
        var bytes = SHA256.HashData(Encoding.UTF8.GetBytes(rawSecret));
        return Convert.ToHexString(bytes).ToLowerInvariant();
    }

    public static bool VerifySecret(string rawSecret, string expectedHexHash)
    {
        var computed = HashSecret(rawSecret);
        return CryptographicOperations.FixedTimeEquals(
            Encoding.ASCII.GetBytes(computed),
            Encoding.ASCII.GetBytes(expectedHexHash ?? string.Empty));
    }
}
