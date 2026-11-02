namespace MesaAyuda.Api.Configuracion;

public sealed class MesaAyudaOptions
{
    public string MongoUri { get; set; } = "mongodb+srv://TU_USUARIO:TU_CONTRASENA@TU_CLUSTER.mongodb.net";
    public string MongoBase { get; set; } = "exponexo_mesa";
    public string JwtEmisor { get; set; } = "http://localhost:8001";
    public string JwtAudiencia { get; set; } = "exponexo";
    public string JwtJwksUrl { get; set; } = "http://localhost:8001/.well-known/jwks.json";
    public string DispositivoCodigoEnrolamiento { get; set; } = "EXN-KIOSCO-2026";
    public int DispositivoSinReporteMinutos { get; set; } = 5;
    public int LecturaRetencionDias { get; set; } = 30;
    public string InternoSecreto { get; set; } = "wZLrMGbejQbI7QzZEXGeqw00Qih-pXNr-DvMNJJcw6o";

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
        return opts;
    }
}
