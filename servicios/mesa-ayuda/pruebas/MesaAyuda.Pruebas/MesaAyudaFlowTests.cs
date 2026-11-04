using System.Net;
using System.Net.Http.Headers;
using System.Net.Http.Json;
using System.Text.Json;
using System.IdentityModel.Tokens.Jwt;
using System.Security.Claims;
using System.Security.Cryptography;
using MesaAyuda.Api.Alertas;
using MesaAyuda.Api.Configuracion;
using MesaAyuda.Api.Datos;
using MesaAyuda.Api.Dispositivos;
using MesaAyuda.Api.Seguridad;
using MesaAyuda.Api.Tickets;
using Microsoft.AspNetCore.Authentication.JwtBearer;
using Microsoft.AspNetCore.Hosting;
using Microsoft.AspNetCore.TestHost;
using Microsoft.AspNetCore.Mvc.Testing;
using Microsoft.Extensions.Configuration;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.DependencyInjection.Extensions;
using Microsoft.IdentityModel.Tokens;
using Xunit;

namespace MesaAyuda.Pruebas;

public sealed class MesaAyudaFlowTests : IClassFixture<HelpdeskApplicationFactory>
{
    private readonly HelpdeskApplicationFactory _factory;

    public MesaAyudaFlowTests(HelpdeskApplicationFactory factory)
    {
        _factory = factory;
    }

    [Fact]
    public async Task TicketLifecycle_SlaCalculation_EscalationToN3_AndResolution()
    {
        using var client = _factory.CreateClient();
        var expositorToken = _factory.CreateToken("usr-expositor-1", "expositor");
        var staffToken = _factory.CreateToken("usr-personal-1", "personal");

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

    [Fact]
    public async Task JwtBearerRejectsInvalidSignatureLifetimeIssuerAudienceAndTokenUse()
    {
        using var client = _factory.CreateClient();
        var valid = _factory.CreateToken("usr-expositor-1", "expositor");
        var tamperedParts = valid.Split('.');
        tamperedParts[2] = (tamperedParts[2][0] == 'A' ? "B" : "A") + tamperedParts[2][1..];
        var tampered = string.Join('.', tamperedParts);
        var invalidTokens = new[]
        {
            tampered,
            _factory.CreateToken("usr-expositor-1", "expositor", expires: DateTimeOffset.UtcNow.AddMinutes(-5)),
            _factory.CreateToken("usr-expositor-1", "expositor", omitExpiration: true),
            _factory.CreateToken("usr-expositor-1", "expositor", issuer: "https://wrong-issuer.test"),
            _factory.CreateToken("usr-expositor-1", "expositor", audience: "wrong-audience"),
            _factory.CreateToken("usr-expositor-1", "expositor", tokenUse: "mfa_pass")
        };

        foreach (var token in invalidTokens)
        {
            using var request = new HttpRequestMessage(HttpMethod.Get, "/v1/tickets");
            request.Headers.Authorization = new AuthenticationHeaderValue("Bearer", token);
            using var response = await client.SendAsync(request);
            Assert.Equal(HttpStatusCode.Unauthorized, response.StatusCode);
        }

    }

    [Fact]
    public void ProductionConfigurationRejectsPlaceholdersAndDevelopmentSecrets()
    {
        var options = new MesaAyudaOptions();
        Assert.Throws<InvalidOperationException>(() => options.ValidateForEnvironment("Production"));

        options.MongoUri = "mongodb+srv://app-user:password@cluster.exponexo.co";
        options.JwtEmisor = "https://identity.exponexo.co";
        options.JwtJwksUrl = "https://identity.exponexo.co/.well-known/jwks.json";
        Assert.Throws<InvalidOperationException>(() => options.ValidateForEnvironment("Production"));

        options.InternoSecreto = "production-internal-secret-value-123456";
        options.DispositivoCodigoEnrolamiento = "production-enrollment-secret-123456";
        Assert.Throws<InvalidOperationException>(() => options.ValidateForEnvironment("Production"));

        options.SnsTemaEventosArn = "arn:aws:sns:us-east-1:000000000000:exponexo-eventos";
        options.ValidateForEnvironment("Production");

        options.ValidateForEnvironment("Development");
    }
}

public sealed class HelpdeskApplicationFactory : WebApplicationFactory<Program>
{
    private readonly RSA _testPrivateKey = RSA.Create(2048);
    private const string TestIssuer = "https://identity.test";
    private const string TestAudience = "exponexo";

    public string CreateToken(
        string subject,
        string role,
        string tokenUse = "access",
        string issuer = TestIssuer,
        string audience = TestAudience,
        DateTimeOffset? expires = null,
        bool omitExpiration = false)
    {
        var claims = new[]
        {
            new Claim("sub", subject),
            new Claim("rol", role),
            new Claim("token_use", tokenUse)
        };
        var signingKey = new RsaSecurityKey(_testPrivateKey) { KeyId = "test-key" };
        var jwt = new JwtSecurityToken(
            issuer,
            audience,
            claims,
            notBefore: DateTime.UtcNow.AddMinutes(-10),
            expires: expires?.UtcDateTime ?? DateTime.UtcNow.AddMinutes(30),
            signingCredentials: new SigningCredentials(signingKey, SecurityAlgorithms.RsaSha256));

        if (omitExpiration)
        {
            jwt.Payload.Remove(JwtRegisteredClaimNames.Exp);
        }

        return new JwtSecurityTokenHandler().WriteToken(jwt);
    }

    protected override void ConfigureWebHost(IWebHostBuilder builder)
    {
        builder.UseEnvironment("Testing");
        builder.ConfigureAppConfiguration((_, configuration) =>
        {
            configuration.AddInMemoryCollection(new Dictionary<string, string?>
            {
                ["JWT_EMISOR"] = TestIssuer,
                ["JWT_AUDIENCIA"] = TestAudience,
                ["JWT_JWKS_URL"] = "https://identity.test/jwks.json",
                ["MesaAyuda:JwtEmisor"] = TestIssuer,
                ["MesaAyuda:JwtAudiencia"] = TestAudience,
                ["MesaAyuda:JwtJwksUrl"] = "https://identity.test/jwks.json"
            });
        });
        builder.ConfigureTestServices(services =>
        {
            services.RemoveAll<IJwksSigningKeyProvider>();
            services.AddSingleton<IJwksSigningKeyProvider>(new FixedJwksSigningKeyProvider(_testPrivateKey));
            services.PostConfigure<JwtBearerOptions>(
                JwtBearerDefaults.AuthenticationScheme,
                jwt =>
                {
                    jwt.TokenValidationParameters.ValidIssuer = TestIssuer;
                    jwt.TokenValidationParameters.ValidAudience = TestAudience;
                });
        });
    }

    protected override void Dispose(bool disposing)
    {
        if (disposing)
        {
            _testPrivateKey.Dispose();
        }
        base.Dispose(disposing);
    }

    private sealed class FixedJwksSigningKeyProvider(RSA rsa) : IJwksSigningKeyProvider
    {
        private readonly SecurityKey _publicKey = new RsaSecurityKey(rsa) { KeyId = "test-key" };

        public IEnumerable<SecurityKey> GetSigningKeys(string? keyId) =>
            keyId == "test-key" ? [_publicKey] : Array.Empty<SecurityKey>();
    }
}
