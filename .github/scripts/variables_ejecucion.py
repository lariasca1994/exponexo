"""Arma la configuración de ejecución de cada servicio a partir del entorno `produccion` de GitHub.

Los valores llegan como variables de entorno del paso (secretos y variables de GitHub) y nunca se
imprimen. Si falta alguno obligatorio, el despliegue se detiene antes de tocar la nube.

Uso:
  variables_ejecucion.py pagos <archivo.json>            -> archivo para `gcloud run deploy --env-vars-file`
  variables_ejecucion.py identidad-reservas <app> <grupo> <imagen> -> secretos, variables e imagen (Azure)
  variables_ejecucion.py mesa-ayuda <app> <grupo> <imagen>         -> secretos, variables e imagen (Azure)
  variables_ejecucion.py eventos <función>                 -> variables de una función Lambda
"""
import json
import os
import subprocess
import sys
from urllib.parse import urlparse

# Por servicio: (secretos, variables visibles, opcionales)
SERVICIOS = {
    "pagos": (
        ["ORACLE_CONTRASENA", "ORACLE_WALLET_ZIP_BASE64", "INTERNO_SECRETO", "COBRO_QR_CLAVE_FIRMA",
         "AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY"],
        ["ORACLE_TNS_ALIAS", "ORACLE_USUARIO", "AWS_REGION", "SNS_TEMA_EVENTOS_ARN", "IDENTIDAD_URL",
         "PORTAL_URL"],
        [],
    ),
    "identidad-reservas": (
        ["SQLSERVER_CONTRASENA", "MFA_CLAVE_CIFRADO", "ENTRADA_QR_CLAVE_FIRMA", "INTERNO_SECRETO",
         "JWT_CLAVE_PRIVADA_PEM", "BREVO_API_KEY", "AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY"],
        ["SQLSERVER_SERVIDOR", "SQLSERVER_BASE", "SQLSERVER_USUARIO", "BREVO_REMITENTE_CORREO",
         "AWS_REGION", "SNS_TEMA_EVENTOS_ARN", "IDENTIDAD_URL", "PORTAL_URL"],
        ["CLOUDINARY_CLOUD_NAME", "CLOUDINARY_API_KEY", "CLOUDINARY_API_SECRET", "USUARIOS_INICIALES"],
    ),
    "mesa-ayuda": (
        ["MONGO_URI", "INTERNO_SECRETO", "DISPOSITIVO_CODIGO_ENROLAMIENTO", "AWS_ACCESS_KEY_ID",
         "AWS_SECRET_ACCESS_KEY"],
        ["MONGO_BASE", "AWS_REGION", "SNS_TEMA_EVENTOS_ARN", "IDENTIDAD_URL", "PORTAL_URL"],
        [],
    ),
    "eventos": (
        ["INTERNO_SECRETO", "BREVO_API_KEY", "TELEGRAM_BOT_TOKEN"],
        ["TELEGRAM_CHAT_ID", "BREVO_REMITENTE_CORREO", "IDENTIDAD_URL", "PAGOS_URL", "MESA_AYUDA_URL",
         "PORTAL_URL"],
        [],
    ),
}
SECRETOS_OPCIONALES = {"CLOUDINARY_API_SECRET", "CLOUDINARY_API_KEY", "USUARIOS_INICIALES"}


def leer(servicio: str) -> tuple[dict[str, str], set[str]]:
    secretos, visibles, opcionales = SERVICIOS[servicio]
    faltan = [n for n in secretos + visibles if not os.environ.get(n, "").strip()]
    if faltan:
        sys.exit(f"::error::Faltan en el entorno produccion de GitHub: {', '.join(faltan)}")
    valores = {n: os.environ[n].strip() for n in secretos + visibles}
    valores.update({n: os.environ[n].strip() for n in opcionales if os.environ.get(n, "").strip()})
    secretas = set(secretos) | (SECRETOS_OPCIONALES & valores.keys())

    identidad = valores["IDENTIDAD_URL"].rstrip("/")
    portal = valores["PORTAL_URL"].rstrip("/")
    derivados = {
        "JWT_EMISOR": identidad,
        "JWT_AUDIENCIA": "exponexo",
        "JWT_JWKS_URL": f"{identidad}/.well-known/jwks.json",
        "CORS_ORIGENES_PERMITIDOS": portal,
        "PORTAL_URL": portal,
    }
    if servicio == "pagos":
        derivados["SPRING_PROFILES_ACTIVE"] = "produccion"
    elif servicio == "identidad-reservas":
        derivados.update({
            "APP_ENTORNO": "produccion",
            "JWT_CLAVE_ID": os.environ.get("JWT_CLAVE_ID") or "exponexo-1",
            "WEBAUTHN_RP_ID": urlparse(portal).hostname or "",
            "WEBAUTHN_ORIGEN_URL": portal,
        })
    elif servicio == "mesa-ayuda":
        derivados["ASPNETCORE_ENVIRONMENT"] = "Production"
    elif servicio == "eventos":
        derivados = {"PORTAL_URL": portal}
    valores.update(derivados)
    return valores, secretas


def az(*args: str) -> None:
    subprocess.run(["az", *args, "--only-show-errors", "--output", "none"], check=True)


def main() -> None:
    servicio = sys.argv[1]
    valores, secretas = leer(servicio)

    if servicio == "pagos":
        with open(sys.argv[2], "w", encoding="utf-8") as archivo:
            json.dump(valores, archivo)
    elif servicio in ("identidad-reservas", "mesa-ayuda"):
        app, grupo, imagen = sys.argv[2], sys.argv[3], sys.argv[4]
        nombre_secreto = {n: n.lower().replace("_", "-") for n in secretas}
        az("containerapp", "secret", "set", "--name", app, "--resource-group", grupo, "--secrets",
           *[f"{nombre_secreto[n]}={valores[n]}" for n in sorted(secretas)])
        variables = [f"{n}=secretref:{nombre_secreto[n]}" if n in secretas else f"{n}={v}"
                     for n, v in sorted(valores.items())]
        # Una sola revisión nueva con la imagen y la configuración juntas
        az("containerapp", "update", "--name", app, "--resource-group", grupo, "--image", imagen,
           "--min-replicas", "0", "--max-replicas", "1", "--set-env-vars", *variables)
    elif servicio == "eventos":
        funcion = sys.argv[2]
        # Una actualización de código o configuración en curso bloquea la siguiente
        subprocess.run(["aws", "lambda", "wait", "function-updated-v2", "--function-name", funcion], check=True)
        subprocess.run(["aws", "lambda", "update-function-configuration", "--function-name", funcion,
                        "--environment", json.dumps({"Variables": valores})],
                       check=True, stdout=subprocess.DEVNULL)
        subprocess.run(["aws", "lambda", "wait", "function-updated-v2", "--function-name", funcion], check=True)
    print(f"Configuración de {servicio} aplicada ({len(valores)} variables, {len(secretas)} secretas).")


if __name__ == "__main__":
    main()
