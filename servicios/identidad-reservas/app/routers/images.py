from typing import Any

from fastapi import APIRouter, Depends, File, Form, UploadFile, status

from app.errors import ProblemDetailError
from app.models.identity import User
from app.security.dependencies import get_current_user
from app.services.cloudinary_service import upload_image_to_cloudinary


router = APIRouter(prefix="/v1/imagenes", tags=["Imágenes"])


@router.post("/subir", status_code=status.HTTP_201_CREATED)
async def upload_image(
    archivo: UploadFile = File(...),
    carpeta: str = Form(default="exponexo"),
    _: User = Depends(get_current_user),
) -> dict[str, Any]:
    content_type = archivo.content_type or ""
    if not (content_type.startswith("image/") or archivo.filename.endswith((".png", ".jpg", ".jpeg", ".svg", ".webp"))):
        raise ProblemDetailError(
            status=400,
            title="Formato de archivo inválido",
            detail="Solo se permite subir imágenes (PNG, JPG, SVG, WebP).",
            problem_type="https://exponexo.co/problemas/archivo-no-imagen",
        )

    file_bytes = await archivo.read()
    if len(file_bytes) > 10 * 1024 * 1024:
        raise ProblemDetailError(
            status=413,
            title="Archivo demasiado pesado",
            detail="El tamaño máximo permitido para imágenes es 10 MB.",
            problem_type="https://exponexo.co/problemas/imagen-muy-grande",
        )

    result = upload_image_to_cloudinary(
        file_bytes=file_bytes,
        filename=archivo.filename or "imagen.jpg",
        folder=carpeta,
    )
    return result
