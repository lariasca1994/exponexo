"""Cuentas fijas de la plataforma (administración, personal y QA).

Llegan en el secreto USUARIOS_INICIALES como una lista JSON de objetos con `correo`, `nombre`,
`rol` y `contrasena`. El workflow de despliegue, después de las migraciones, garantiza que
existan, estén activas, con el correo verificado, el rol indicado y la verificación en dos pasos
por correo activa (no lo hace el contenedor al arrancar: así no despierta la base). Son las únicas
cuentas con rol `personal` o `administrador`: el registro público solo crea visitantes o
expositores.
"""
import json
import logging

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.identity import MfaFactor, User
from app.security.passwords import hash_password, verify_password

logger = logging.getLogger("exponexo.identidad.usuarios_iniciales")

VALID_ROLES = {"visitante", "expositor", "personal", "administrador"}


def parse_initial_users(raw: str) -> list[dict[str, str]]:
    if not raw.strip():
        return []
    users = json.loads(raw)
    for user in users:
        missing = {"correo", "nombre", "rol", "contrasena"} - user.keys()
        if missing:
            raise ValueError(f"USUARIOS_INICIALES: faltan campos {sorted(missing)}")
        if user["rol"] not in VALID_ROLES:
            raise ValueError(f"USUARIOS_INICIALES: rol inválido '{user['rol']}'")
    return users


def ensure_initial_users(db: Session, users: list[dict[str, str]]) -> int:
    """Crea o ajusta cada cuenta fija; devuelve cuántas cambiaron."""
    changed = 0
    for data in users:
        email = data["correo"].strip().lower()
        user = db.scalar(select(User).where(User.correo == email))
        if user is None:
            user = User(
                correo=email,
                nombre=data["nombre"].strip(),
                hash_contrasena=hash_password(data["contrasena"]),
                rol=data["rol"],
                activo=True,
                correo_verificado=True,
            )
            db.add(user)
            db.flush()
            changed += 1
        else:
            updated = False
            if user.rol != data["rol"]:
                user.rol, updated = data["rol"], True
            if not user.activo or not user.correo_verificado:
                user.activo, user.correo_verificado, updated = True, True, True
            if not verify_password(user.hash_contrasena, data["contrasena"]):
                user.hash_contrasena, updated = hash_password(data["contrasena"]), True
            changed += int(updated)

        has_factor = db.scalar(
            select(MfaFactor).where(MfaFactor.usuario_id == user.id, MfaFactor.activo.is_(True))
        )
        if has_factor is None:
            db.add(MfaFactor(usuario_id=user.id, tipo="correo", secreto_cifrado=None, activo=True, preferido=True))
    db.commit()
    return changed


def main() -> None:
    """Lo ejecuta el workflow de despliegue después de las migraciones (no el contenedor)."""
    from app.config import get_settings
    from app.db import SessionLocal

    users = parse_initial_users(get_settings().initial_users_json)
    if not users:
        print("Sin USUARIOS_INICIALES: no hay cuentas fijas que verificar")
        return
    with SessionLocal() as db:
        changed = ensure_initial_users(db, users)
    print(f"Cuentas fijas verificadas: {len(users)} ({changed} con cambios)")


if __name__ == "__main__":
    main()
