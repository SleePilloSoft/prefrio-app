"""Administra tokens de dispositivo (Raspberry de tablero).

Uso, desde la raíz del proyecto:
    python -m scripts.dispositivos crear prefrio1
    python -m scripts.dispositivos revocar prefrio1
"""

import argparse
import secrets
import sys
from datetime import datetime, timezone

from sqlalchemy import select

from app.auth import hash_token
from app.db import SessionLocal
from app.models import Dispositivo


def crear(nombre: str) -> None:
    token = secrets.token_urlsafe(32)
    with SessionLocal() as session:
        session.add(Dispositivo(nombre=nombre, token_hash=hash_token(token)))
        session.commit()
    print(f"Token para {nombre} (guárdelo ahora, no se vuelve a mostrar):\n{token}")


def revocar(nombre: str) -> None:
    with SessionLocal() as session:
        dispositivo = session.scalar(select(Dispositivo).where(Dispositivo.nombre == nombre))
        if dispositivo is None:
            sys.exit(f"No existe el dispositivo {nombre}")
        dispositivo.revocado_utc = datetime.now(timezone.utc)
        session.commit()
    print(f"Dispositivo {nombre} revocado.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("accion", choices=["crear", "revocar"])
    parser.add_argument("nombre")
    args = parser.parse_args()
    crear(args.nombre) if args.accion == "crear" else revocar(args.nombre)
