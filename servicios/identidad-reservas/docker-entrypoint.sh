#!/bin/sh
# Arranque del contenedor: materializa la llave JWT desde su secreto y levanta la API.
# Las migraciones las aplica el workflow de despliegue antes de publicar la revisión, para que el
# contenedor arranque rápido. Si la configuración es inválida, el contenedor no arranca.
set -eu

if [ -n "${JWT_CLAVE_PRIVADA_PEM:-}" ]; then
  umask 077
  mkdir -p /tmp/claves
  printf '%s\n' "$JWT_CLAVE_PRIVADA_PEM" > /tmp/claves/jwt_privada.pem
  export JWT_CLAVE_PRIVADA_RUTA=/tmp/claves/jwt_privada.pem
  unset JWT_CLAVE_PRIVADA_PEM
fi

exec uvicorn app.main:create_app --factory --host 0.0.0.0 --port "${PORT:-8001}" \
  --proxy-headers --forwarded-allow-ips='*'
