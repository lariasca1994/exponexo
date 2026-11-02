using System.Net;
using System.Net.Http.Headers;
using System.Net.Http.Json;
using System.Text;
using System.Text.Json;
using MesaAyuda.Api.Alertas;
using MesaAyuda.Api.Datos;
using MesaAyuda.Api.Dispositivos;
using MesaAyuda.Api.Tickets;
using Microsoft.AspNetCore.Mvc.Testing;
using Microsoft.Extensions.DependencyInjection;
using Xunit;

namespace MesaAyuda.Pruebas;

public sealed class MesaAyudaFlowTests : IClassFixture<WebApplicationFactory<Program>>
{
    private readonly WebApplicationFactory<Program> _factory;

    public MesaAyudaFlowTests(WebApplicationFactory<Program> factory)
    {
        _factory = factory;
    }

    private static string BuildFakeJwt(string sub, string rol)
    {
        var header = Base64UrlEncode("""{"alg":"RS256","typ":"JWT"}""");
        var exp = DateTimeOffset.UtcNow.AddMinutes(30).ToUnixTimeSeconds();
        var payload = Base64UrlEncode(JsonSerializer.Serialize(new
        {
            sub,
            rol,
            token_use = "access",
            exp
        }));
        return $"{header}.{payload}.firma-prueba";
    }

    private static string Base64UrlEncode(string json) =>
        Convert.ToBase64String(Encoding.UTF8.GetBytes(json))
            .Replace('+', '-')
            .Replace('/', '_')
            .TrimEnd('=');

    [Fact]
    public async Task TicketLifecycle_SlaCalculation_EscalationToN3_AndResolution()
    {
        using var client = _factory.CreateClient();
        var expositorToken = BuildFakeJwt("usr-expositor-1", "expositor");
        var staffToken = BuildFakeJwt("usr-personal-1", "personal");

        // 1. Sin token -> 401
        var unauthRes = await client.GetAsync("/v1/tickets");
        Assert.Equal(HttpStatusCode.Unauthorized, unauthRes.StatusCode);

        // 2. Expositor crea ticket de prioridad 'critica' (SLA = 60 min)
        using var createReq = new HttpRequestMessage(HttpMethod.Post, "/v1/tickets")
        {
            Content = JsonContent.Create(new
            {
                evento_id = "ev-1",
                ubicacion = "Pabellón 1 · Stand A-12",
                categoria = "electrico",
                prioridad = "critica",
                descripcion = "Corte de energía en la vitrina refrigerada"
            })
        };
        createReq.Headers.Authorization = new AuthenticationHeaderValue("Bearer", expositorToken);

        var createRes = await client.SendAsync(createReq);
        Assert.Equal(HttpStatusCode.Created, createRes.StatusCode);
        var created = await createRes.Content.ReadFromJsonAsync<TicketDocument>();
        Assert.NotNull(created);
        Assert.Equal("abierto", created!.Estado);
        Assert.Equal("N1", created.NivelActual);
        Assert.Single(created.Historial);

        var expectedMinutes = (created.SlaVenceEn - created.CreadoEn).TotalMinutes;
        Assert.InRange(expectedMinutes, 59.5, 60.5);

        // 3. Personal toma el ticket -> en_atencion
        using var takeReq = new HttpRequestMessage(HttpMethod.Post, $"/v1/tickets/{created.Id}/tomar");
        takeReq.Headers.Authorization = new AuthenticationHeaderValue("Bearer", staffToken);
        var takeRes = await client.SendAsync(takeReq);
        Assert.Equal(HttpStatusCode.OK, takeRes.StatusCode);

        // 4. Escalar N1 -> N2 y luego N2 -> N3; tercer intento -> 409 Conflict
        using var esc1 = new HttpRequestMessage(HttpMethod.Post, $"/v1/tickets/{created.Id}/escalar")
        {
            Content = JsonContent.Create(new { nota = "Requiere electricista de planta N2" })
        };
        esc1.Headers.Authorization = new AuthenticationHeaderValue("Bearer", staffToken);
        var esc1Res = await client.SendAsync(esc1);
        Assert.Equal(HttpStatusCode.OK, esc1Res.StatusCode);

        using var esc2 = new HttpRequestMessage(HttpMethod.Post, $"/v1/tickets/{created.Id}/escalar")
        {
            Content = JsonContent.Create(new { nota = "Requiere ingeniero de subestación N3" })
        };
        esc2.Headers.Authorization = new AuthenticationHeaderValue("Bearer", staffToken);
        var esc2Res = await client.SendAsync(esc2);
        Assert.Equal(HttpStatusCode.OK, esc2Res.StatusCode);

        using var esc3 = new HttpRequestMessage(HttpMethod.Post, $"/v1/tickets/{created.Id}/escalar")
        {
            Content = JsonContent.Create(new { nota = "Intento por encima de N3" })
        };
        esc3.Headers.Authorization = new AuthenticationHeaderValue("Bearer", staffToken);
        var esc3Res = await client.SendAsync(esc3);
        Assert.Equal(HttpStatusCode.Conflict, esc3Res.StatusCode);

        // 5. Resolver el ticket dentro del tiempo del SLA -> sla_cumplido == true y 5 entradas en historial
        using var resolveReq = new HttpRequestMessage(HttpMethod.Post, $"/v1/tickets/{created.Id}/resolver")
        {
            Content = JsonContent.Create(new { nota = "Breakers reemplazados y tensión estabilizada" })
        };
        resolveReq.Headers.Authorization = new AuthenticationHeaderValue("Bearer", staffToken);
        var resolveRes = await client.SendAsync(resolveReq);
        Assert.Equal(HttpStatusCode.OK, resolveRes.StatusCode);

        var resolved = await resolveRes.Content.ReadFromJsonAsync<TicketDocument>();
        Assert.NotNull(resolved);
        Assert.Equal("resuelto", resolved!.Estado);
        Assert.Equal("N3", resolved.NivelActual);
        Assert.True(resolved.SlaCumplido);
        Assert.Equal(5, resolved.Historial.Count);
    }

    [Fact]
    public async Task DeviceEnrollment_Readings_AndSingleOfflineTicketDetection()
    {
        using var client = _factory.CreateClient();

        // 1. Enrolar kiosco con código válido
        var enrollRes = await client.PostAsJsonAsync("/v1/dispositivos/enrolar", new
        {
            codigo_enrolamiento = "EXN-KIOSCO-2026",
            codigo = "KIOSCO-SUR-01",
            tipo = "kiosco",
            ubicacion = "Entrada Sur",
            version_firmware = "2.1.0"
        });
        Assert.Equal(HttpStatusCode.Created, enrollRes.StatusCode);
        var enrolled = await enrollRes.Content.ReadFromJsonAsync<EnrollDeviceResponse>();
        Assert.NotNull(enrolled);
        Assert.False(string.IsNullOrWhiteSpace(enrolled!.TokenDispositivo));

        // 2. Enviar lectura autenticada con X-Token-Dispositivo -> 202 Accepted
        using var readReq = new HttpRequestMessage(HttpMethod.Post, $"/v1/dispositivos/{enrolled.DispositivoId}/lecturas")
        {
            Content = JsonContent.Create(new
            {
                cpu_porcentaje = 28.5,
                memoria_porcentaje = 44.0,
                temperatura_c = 41.2,
                conectado = true
            })
        };
        readReq.Headers.Add("X-Token-Dispositivo", enrolled.TokenDispositivo);
        var readRes = await client.SendAsync(readReq);
        Assert.Equal(HttpStatusCode.Accepted, readRes.StatusCode);

        // 3. Simular paso de 10 minutos sin reporte: abre 1 ticket en el primer barrido y 0 en el segundo
        var monitor = _factory.Services.GetRequiredService<DeviceAndSlaMonitorService>();
        var futureTime = DateTimeOffset.UtcNow.AddMinutes(10);

        var firstScan = await monitor.RunScanCycleAsync(futureTime);
        Assert.Equal(1, firstScan.OfflineDevicesDetected);

        var secondScan = await monitor.RunScanCycleAsync(futureTime.AddMinutes(1));
        Assert.Equal(0, secondScan.OfflineDevicesDetected);

        var store = _factory.Services.GetRequiredService<IMesaAyudaStore>();
        var outbox = await store.ListPendingOutboxAsync();
        Assert.Contains(outbox, o => o.Tipo == "dispositivo.caido");
    }
}
