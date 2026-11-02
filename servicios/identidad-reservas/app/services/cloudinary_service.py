import hashlib
import logging
import time
from typing import Any

import httpx

from app.config import settings
from app.errors import ProblemDetailError

logger = logging.getLogger("exponexo.identidad.cloudinary")


def upload_image_to_cloudinary(
    file_bytes: bytes,
    filename: str,
    folder: str = "exponexo",
    http_client: httpx.Client | None = None,
) -> dict[str, Any]:
    """
    Sube una imagen a Cloudinary mediante su API REST v1_1.
    Si no hay credenciales configuradas en entorno local, devuelve una URL simulada
    sin fallar ni detener las pruebas.
    """
    cloud_name = settings.cloudinary_cloud_name.strip()
    api_key = settings.cloudinary_api_key.strip()
    api_secret = settings.cloudinary_api_secret.strip()

    if not cloud_name or not api_key or not api_secret or cloud_name.startswith("TU_"):
        file_hash = hashlib.sha256(file_bytes[:256]).hexdigest()[:16]
        mock_url = f"https://res.cloudinary.com/exponexo-dev/image/upload/v1/{folder}/{file_hash}_{filename}"
        logger.info("Modo local sin Cloudinary real: imagen simulada generada -> %s", mock_url)
        return {
            "secure_url": mock_url,
            "public_id": f"{folder}/{file_hash}_{filename}",
            "formato": filename.split(".")[-1] if "." in filename else "jpg",
            "modo": "simulado",
        }

    timestamp = str(int(time.time()))
    # Firma según la documentación oficial de Cloudinary: sha1 de "folder=...&timestamp=...<api_secret>"
    signature_str = f"folder={folder}&timestamp={timestamp}{api_secret}"
    signature = hashlib.sha1(signature_str.encode("utf-8")).hexdigest()

    upload_url = f"https://api.cloudinary.com/v1_1/{cloud_name}/image/upload"
    data = {
        "api_key": api_key,
        "timestamp": timestamp,
        "signature": signature,
        "folder": folder,
    }
    files = {"file": (filename, file_bytes)}

    own_client = http_client is None
    client = http_client or httpx.Client(timeout=15.0)
    try:
        response = client.post(upload_url, data=data, files=files)
        if response.status_code >= 400:
            raise ProblemDetailError(
                status=502,
                title="Error al subir imagen a Cloudinary",
                detail=f"Cloudinary respondió con código {response.status_code}: {response.text}",
                problem_type="https://exponexo.co/problemas/error-cloudinary",
            )
        payload = response.json()
        return {
            "secure_url": payload.get("secure_url"),
            "public_id": payload.get("public_id"),
            "formato": payload.get("format"),
            "ancho": payload.get("width"),
            "alto": payload.get("height"),
            "bytes": payload.get("bytes"),
        }
    except Exception as exc:
        if isinstance(exc, ProblemDetailError):
            raise
        raise ProblemDetailError(
            status=502,
            title="Error de conexión con Cloudinary",
            detail=str(exc),
            problem_type="https://exponexo.co/problemas/conexion-cloudinary",
        ) from exc
    finally:
        if own_client:
            client.close()
