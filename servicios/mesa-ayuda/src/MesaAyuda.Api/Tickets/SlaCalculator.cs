namespace MesaAyuda.Api.Tickets;

public static class SlaCalculator
{
    private static readonly IReadOnlyDictionary<string, SlaPolicyDocument> DefaultPolicies =
        new Dictionary<string, SlaPolicyDocument>(StringComparer.OrdinalIgnoreCase)
        {
            ["baja"] = new() { Prioridad = "baja", MinutosRespuestaN1 = 60, MinutosResolucion = 480 },
            ["media"] = new() { Prioridad = "media", MinutosRespuestaN1 = 30, MinutosResolucion = 240 },
            ["alta"] = new() { Prioridad = "alta", MinutosRespuestaN1 = 15, MinutosResolucion = 120 },
            ["critica"] = new() { Prioridad = "critica", MinutosRespuestaN1 = 5, MinutosResolucion = 60 }
        };

    public static IReadOnlyCollection<SlaPolicyDocument> GetDefaultPolicies() =>
        DefaultPolicies.Values.ToList();

    public static SlaPolicyDocument GetPolicy(string prioridad, IEnumerable<SlaPolicyDocument>? customPolicies = null)
    {
        var normalized = (prioridad ?? "media").Trim().ToLowerInvariant();
        if (customPolicies is not null)
        {
            var found = customPolicies.FirstOrDefault(p =>
                string.Equals(p.Prioridad, normalized, StringComparison.OrdinalIgnoreCase));
            if (found is not null)
            {
                return found;
            }
        }

        return DefaultPolicies.TryGetValue(normalized, out var policy)
            ? policy
            : DefaultPolicies["media"];
    }

    public static DateTimeOffset CalculateDueAt(
        DateTimeOffset createdAt,
        string prioridad,
        IEnumerable<SlaPolicyDocument>? customPolicies = null)
    {
        var policy = GetPolicy(prioridad, customPolicies);
        return createdAt.AddMinutes(policy.MinutosResolucion);
    }

    public static string? NextEscalationLevel(string currentLevel) =>
        (currentLevel ?? "N1").Trim().ToUpperInvariant() switch
        {
            "N1" => "N2",
            "N2" => "N3",
            _ => null
        };
}
