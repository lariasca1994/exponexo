# Eventos entre servicios

**Python**

Dos funciones reciben los eventos que publican los demás servicios: `repartidor/` los lleva a la API
que corresponde y `avisos/` envía cada aviso por correo y por Telegram a la persona afectada. Si un
canal falla, el otro sale igual.

## Comandos

Desde esta carpeta:

```powershell
python -m pip install -r repartidor/requirements.txt
python -m pip install -r avisos/requirements.txt
python -m pytest pruebas -v
```

Se publica sola desde GitHub en cada cambio a `main`, si pasan las pruebas.
