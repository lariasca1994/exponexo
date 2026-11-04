# Eventos entre servicios

**Python · Amazon SQS · AWS Lambda**

El servicio contiene dos consumidores: `repartidor/funcion.py` enruta eventos a las APIs internas;
`avisos/funcion.py` envía correo con Brevo y mensajes de Telegram. Cada función mantiene su propio
`requirements.txt`; sus pruebas viven en `pruebas/`.

Los tipos de evento y varios campos actuales conservan nombres en español. La transición a los
nombres ingleses definidos por ADR-012 y [EVENTOS.md](../../docs/EVENTOS.md) debe coordinar
productores, consumidores e idempotencia; no se puede hacer solo en una Lambda.

## Comandos

Desde esta carpeta:

```powershell
python -m pip install -r repartidor/requirements.txt
python -m pip install -r avisos/requirements.txt
python -m pytest pruebas -v
```

Para empaquetar y desplegar, consulta `.github/workflows/eventos.yml`. El workflow crea paquetes
separados para cada función, autentica por OIDC y los actualiza en AWS Lambda al publicar en
`main`, junto con sus variables y la retención de logs de 14 días. Los servicios publican en un
tema SNS que entrega cada evento, sin envoltura, a una cola por función; tras 5 intentos fallidos
el mensaje pasa a la cola de errores de esa función. Las colas, los activadores y los roles los
crea [infra/aws/crear.sh](../../infra/aws/crear.sh).
