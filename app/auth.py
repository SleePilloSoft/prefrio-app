import hashlib

from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import get_session
from app.models import Dispositivo

bearer = HTTPBearer(auto_error=False)


def hash_token(token: str) -> str:
    """El servidor guarda solo el hash del token, nunca el token."""
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def dispositivo_autenticado(
    credenciales: HTTPAuthorizationCredentials | None = Depends(bearer),
    session: Session = Depends(get_session),
) -> Dispositivo:
    if credenciales is None:
        raise HTTPException(status_code=401, detail="token de dispositivo requerido")
    dispositivo = session.scalar(
        select(Dispositivo).where(Dispositivo.token_hash == hash_token(credenciales.credentials))
    )
    if dispositivo is None or dispositivo.revocado_utc is not None:
        raise HTTPException(status_code=401, detail="token inválido o revocado")
    return dispositivo
