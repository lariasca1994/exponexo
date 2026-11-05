namespace MesaAyuda.Api.Configuracion;

public sealed class MesaAyudaOptions
{
    public const string DevelopmentEnrollmentCode = "EXN-KIOSCO-2026";
    // Solo para desarrollo local: en producción se rechaza (ValidateForEnvironment)
    public const string DevelopmentInternalSecret = "desarrollo-interno-no-usar-en-produccion";

    public string MongoUri { get; set; } = "mongodb+srv://TU_USUARIO:TU_CONTRASENA@TU_CLUSTER.mongodb.net";
    public string MongoBase { get; set; } = "exponexo_mesa";
    public string JwtEmisor { get; set; } = "http://localhost:8001";
    public string JwtAudiencia { get; set; } = "exponexo";
    public string JwtJwksUrl { get; set; } = "http://localhost:8001/.well-known/jwks.json";
    public string DispositivoCodigoEnrolamiento { get; set; } = DevelopmentEnrollmentCode;
    public int DispositivoSinReporteMinutos { get; set; } = 5;
    public int LecturaRetencionDias { get; set; } = 15;
    public string InternoSecreto { get; set; } = DevelopmentInternalSecret;
    public string SnsTemaEventosArn { get; set; } = string.Empty;

    public static MesaAyudaOptions FromConfiguration(IConfiguration config)
    {
        var opts = new MesaAyudaOptions();
        config.GetSection("MesaAyuda").Bind(opts);

        opts.MongoUri = config["MONGO_URI"] ?? opts.MongoUri;
        opts.MongoBase = config["MONGO_BASE"] ?? opts.MongoBase;
        opts.JwtEmisor = config["JWT_EMISOR"] ?? opts.JwtEmisor;
        opts.JwtAudiencia = config["JWT_AUDIENCIA"] ?? opts.JwtAudiencia;
        opts.JwtJwksUrl = config["JWT_JWKS_URL"] ?? opts.JwtJwksUrl;
        opts.DispositivoCodigoEnrolamiento = config["DISPOSITIVO_CODIGO_ENROLAMIENTO"] ?? opts.DispositivoCodigoEnrolamiento;
        if (int.TryParse(config["DISPOSITIVO_SIN_REPORTE_MINUTOS"], out var sinReporte))
        {
            opts.DispositivoSinReporteMinutos = sinReporte;
        }
        if (int.TryParse(config["LECTURA_RETENCION_DIAS"], out var retencion))
        {
            opts.LecturaRetencionDias = retencion;
        }
        opts.InternoSecreto = config["INTERNO_SECRETO"] ?? opts.InternoSecreto;
        opts.SnsTemaEventosArn = config["SNS_TEMA_EVENTOS_ARN"] ?? opts.SnsTemaEventosArn;
        return opts;
    }

    public static bool IsPlaceholderMongoUri(string? value)
    {
        if (string.IsNullOrWhiteSpace(value)
            || value.Contains("TU_", StringComparison.OrdinalIgnoreCase)
            || value.Contains("changeme", StringComparison.OrdinalIgnoreCase)
            || value.Contains("example", StringComparison.OrdinalIgnoreCase))
        {
            return true;
        }

        return !Uri.TryCreate(value, UriKind.Absolute, out var uri)
            || (uri.Scheme != "mongodb" && uri.Scheme != "mongodb+srv")
            || string.IsNullOrWhiteSpace(uri.Host);
    }

    public void ValidateForEnvironment(string environmentName)
    {
        var production = string.Equals(environmentName, "Production", StringComparison.OrdinalIgnoreCase);
        if (!production && (string.Equals(environmentName, "Development", StringComparison.OrdinalIgnoreCase)
                            || string.Equals(environmentName, "Testing", StringComparison.OrdinalIgnoreCase))
                         && IsPlaceholderMongoUri(MongoUri))
        {
            return;
        }

        if (IsPlaceholderMongoUri(MongoUri))
        {
            throw new InvalidOperationException("MONGO_URI debe configurarse con un URI MongoDB valido.");
        }

        if (production)
        {
            if (string.IsNullOrWhiteSpace(InternoSecreto)
                || InternoSecreto.Length < 32
                || InternoSecreto == DevelopmentInternalSecret)
            {
                throw new InvalidOperationException("INTERNO_SECRETO debe ser un secreto de produccion de al menos 32 caracteres.");
            }

            if (string.IsNullOrWhiteSpace(DispositivoCodigoEnrolamiento)
                || DispositivoCodigoEnrolamiento.Length < 32
                || DispositivoCodigoEnrolamiento == DevelopmentEnrollmentCode)
            {
                throw new InvalidOperationException("DISPOSITIVO_CODIGO_ENROLAMIENTO debe ser un secreto de produccion de al menos 32 caracteres.");
            }

            if (!Uri.TryCreate(JwtJwksUrl, UriKind.Absolute, out var jwksUri)
                || jwksUri.Scheme != Uri.UriSchemeHttps
                || !Uri.TryCreate(JwtEmisor, UriKind.Absolute, out var issuerUri)
                || issuerUri.Scheme != Uri.UriSchemeHttps
                || string.IsNullOrWhiteSpace(JwtAudiencia))
            {
                throw new InvalidOperationException("JWT_JWKS_URL y JWT_EMISOR deben ser HTTPS; JWT_AUDIENCIA debe estar configurada.");
            }

            if (!SnsTemaEventosArn.StartsWith("arn:aws:sns:", StringComparison.Ordinal))
            {
                throw new InvalidOperationException("SNS_TEMA_EVENTOS_ARN debe configurarse en produccion.");
            }
        }
    }
}
