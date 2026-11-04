import asyncio
from contextlib import asynccontextmanager
import uuid

from fastapi import FastAPI, Request, Response
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.db import Base, engine
from app.errors import (
    ProblemDetailError,
    problem_detail_exception_handler,
    validation_exception_handler,
)
from app.routers import (
    accounts,
    catalog,
    health,
    images,
    internal,
    profile,
    reservations,
    session,
    tickets_agenda,
)
from app.services.outbox_publisher import run_outbox_publisher_loop


def create_app(init_local_db: bool = True) -> FastAPI:
    settings = get_settings()

    @asynccontextmanager
    async def lifespan(_: FastAPI):
        if init_local_db and settings.sqlalchemy_database_uri.startswith("sqlite"):
            Base.metadata.create_all(bind=engine)
        publisher = (
            asyncio.create_task(run_outbox_publisher_loop()) if settings.sns_events_topic_arn else None
        )
        yield
        if publisher:
            publisher.cancel()

    app = FastAPI(
        title="ExpoNexo · Identidad, Reservas y Agenda",
        version="1.0.0",
        description="Servicio central de cuentas, MFA, WebAuthn, emisión de JWT RS256 (JWKS) y reservas.",
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["X-Correlation-Id"],
    )

    @app.middleware("http")
    async def correlation_id_middleware(request: Request, call_next) -> Response:
        correlation_id = request.headers.get("X-Correlation-Id") or str(uuid.uuid4())
        request.state.correlation_id = correlation_id
        response: Response = await call_next(request)
        response.headers["X-Correlation-Id"] = correlation_id
        return response

    app.add_exception_handler(ProblemDetailError, problem_detail_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)

    app.include_router(health.router)
    app.include_router(accounts.router)
    app.include_router(session.router)
    app.include_router(profile.router)
    app.include_router(catalog.router)
    app.include_router(reservations.router)
    app.include_router(tickets_agenda.router)
    app.include_router(images.router)
    app.include_router(internal.router)

    return app


app = create_app()
