from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse


class ProblemDetailError(Exception):
    def __init__(
        self,
        status: int,
        title: str,
        detail: str,
        problem_type: str = "about:blank",
    ) -> None:
        super().__init__(detail)
        self.status = status
        self.title = title
        self.detail = detail
        self.problem_type = problem_type


async def problem_detail_exception_handler(
    request: Request,
    exc: ProblemDetailError,
) -> JSONResponse:
    correlation_id = getattr(request.state, "correlation_id", None)
    body = {
        "type": exc.problem_type,
        "title": exc.title,
        "status": exc.status,
        "detail": exc.detail,
        "instance": str(request.url.path),
    }
    if correlation_id:
        body["correlacion_id"] = correlation_id
    return JSONResponse(
        status_code=exc.status,
        content=body,
        media_type="application/problem+json",
    )


async def validation_exception_handler(
    request: Request,
    exc: RequestValidationError,
) -> JSONResponse:
    correlation_id = getattr(request.state, "correlation_id", None)
    errors = exc.errors()
    first_msg = errors[0].get("msg", "Datos de entrada inválidos.") if errors else "Datos inválidos."
    body = {
        "type": "https://exponexo.co/problemas/validacion",
        "title": "Datos de solicitud inválidos",
        "status": 422,
        "detail": first_msg,
        "instance": str(request.url.path),
    }
    if correlation_id:
        body["correlacion_id"] = correlation_id
    return JSONResponse(
        status_code=422,
        content=body,
        media_type="application/problem+json",
    )
