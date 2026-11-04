using System.Net.Http;
using System.Text.Json;
using Microsoft.IdentityModel.Tokens;

namespace MesaAyuda.Api.Seguridad;

public interface IJwksSigningKeyProvider
{
    IEnumerable<SecurityKey> GetSigningKeys(string? keyId);
}

public sealed class JwksSigningKeyProvider(string jwksUrl) : IJwksSigningKeyProvider
{
    private static readonly TimeSpan CacheDuration = TimeSpan.FromMinutes(5);
    // Identidad escala a cero: si el JWKS no responde, se reintenta pronto en vez de rechazar
    // todos los tokens durante el periodo completo de caché.
    private static readonly TimeSpan RetryAfterFailure = TimeSpan.FromSeconds(10);
    private readonly object _sync = new();
    private readonly HttpClient _httpClient = new() { Timeout = TimeSpan.FromSeconds(30) };
    private IReadOnlyCollection<SecurityKey> _cachedKeys = Array.Empty<SecurityKey>();
    private DateTimeOffset _lastRefresh = DateTimeOffset.MinValue;

    public IEnumerable<SecurityKey> GetSigningKeys(string? keyId)
    {
        lock (_sync)
        {
            var matchingKeys = FindMatchingKeys(keyId);
            if (matchingKeys.Count > 0)
            {
                return matchingKeys;
            }

            var wait = _cachedKeys.Count == 0 ? RetryAfterFailure : CacheDuration;
            if (DateTimeOffset.UtcNow - _lastRefresh < wait)
            {
                return Array.Empty<SecurityKey>();
            }

            RefreshKeys();
            return FindMatchingKeys(keyId);
        }
    }

    private List<SecurityKey> FindMatchingKeys(string? keyId) =>
        _cachedKeys
            .Where(key => key is JsonWebKey jwk
                          && jwk.Kty == "RSA"
                          && jwk.Use == "sig"
                          && jwk.Alg == SecurityAlgorithms.RsaSha256
                          && !string.IsNullOrWhiteSpace(jwk.Kid)
                          && (string.IsNullOrWhiteSpace(keyId) || jwk.Kid == keyId))
            .ToList();

    private void RefreshKeys()
    {
        _lastRefresh = DateTimeOffset.UtcNow;
        try
        {
            var json = _httpClient.GetStringAsync(jwksUrl).GetAwaiter().GetResult();
            var keySet = new JsonWebKeySet(json);
            _cachedKeys = keySet.Keys.Cast<SecurityKey>().ToArray();
        }
        catch (HttpRequestException)
        {
            // Se conservan las llaves anteriores; el siguiente intento llega tras RetryAfterFailure.
        }
        catch (TaskCanceledException)
        {
            // Se conservan las llaves anteriores; el siguiente intento llega tras RetryAfterFailure.
        }
        catch (JsonException)
        {
            // Se conservan las llaves anteriores; el siguiente intento llega tras RetryAfterFailure.
        }
    }
}
