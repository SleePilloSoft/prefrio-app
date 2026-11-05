import re
from datetime import timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth import dispositivo_autenticado
from app.db import get_session
from app.models import Dispositivo, Lectura, Sensor
from app.schemas import POSICIONES_VALIDAS, LecturaIn, LoteIn, RechazoOut, RespuestaOut

router = APIRouter()
TUNEL_RE = re.compile(r"^PREFRIO-TUNEL-[A-Za-z0-9_-]+$")


def _motivo_rechazo(lectura: LecturaIn) -> str | None:
    if lectura.fecha_utc.tzinfo is None:
        return "fecha sin zona horaria"
    if lectura.posicion is not None and lectura.posicion not in POSICIONES_VALIDAS:
        return "posicion no valida"
    return None


@router.post("/lecturas", response_model=RespuestaOut)
def recibir_lecturas(
    lote: LoteIn,
    dispositivo: Dispositivo = Depends(dispositivo_autenticado),
    session: Session = Depends(get_session),
) -> RespuestaOut:
    if lote.dispositivo != dispositivo.nombre:
        raise HTTPException(status_code=403, detail="dispositivo no coincide con el token")
    if not TUNEL_RE.match(lote.tunel):
        raise HTTPException(status_code=422, detail="tunel no valido")

    ya_recibidos = set(
        session.scalars(
            select(Lectura.id_local).where(
                Lectura.dispositivo == lote.dispositivo,
                Lectura.id_local.in_([l.id_local for l in lote.lecturas]),
            )
        )
    )
    aceptadas: list[int] = []
    duplicadas: list[int] = []
    rechazadas: list[RechazoOut] = []

    for lectura in lote.lecturas:
        if lectura.id_local in ya_recibidos:
            duplicadas.append(lectura.id_local)
            continue
        motivo = _motivo_rechazo(lectura)
        if motivo:
            rechazadas.append(RechazoOut(id_local=lectura.id_local, motivo=motivo))
            continue

        if session.get(Sensor, lectura.sensor_id) is None:
            session.add(
                Sensor(
                    sensor_id=lectura.sensor_id,
                    tipo=lectura.tipo,
                    tunel=lote.tunel,
                    posicion=lectura.posicion,
                )
            )
        session.add(
            Lectura(
                dispositivo=lote.dispositivo,
                id_local=lectura.id_local,
                sensor_id=lectura.sensor_id,
                tipo=lectura.tipo,
                tunel=lote.tunel,
                posicion=lectura.posicion,
                fecha_utc=lectura.fecha_utc.astimezone(timezone.utc),
                temperatura=lectura.temperatura,
                humedad=lectura.humedad,
            )
        )
        ya_recibidos.add(lectura.id_local)
        aceptadas.append(lectura.id_local)

    session.commit()
    return RespuestaOut(aceptadas=aceptadas, duplicadas=duplicadas, rechazadas=rechazadas)
