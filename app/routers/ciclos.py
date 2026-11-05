from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.auth import dispositivo_autenticado
from app.db import get_session
from app.models import AsignacionPosicion, Ciclo
from app.routers.lecturas import TUNEL_RE
from app.schemas import POSICIONES_VALIDAS
from app.schemas_ciclos import AsignacionesIn, CicloIn, CicloOut

router = APIRouter()
POSICIONES_PALLET = POSICIONES_VALIDAS - {"TUNEL"}


def _ciclo_activo(session: Session, tunel: str) -> Ciclo | None:
    return session.scalar(
        select(Ciclo).where(Ciclo.tunel == tunel, Ciclo.terminado_utc.is_(None))
    )


def _salida(ciclo: Ciclo) -> CicloOut:
    return CicloOut(
        id=ciclo.id,
        tunel=ciclo.tunel,
        iniciado_utc=ciclo.iniciado_utc,
        terminado_utc=ciclo.terminado_utc,
    )


@router.post("/ciclos", response_model=CicloOut, status_code=201)
def abrir_ciclo(
    datos: CicloIn,
    _=Depends(dispositivo_autenticado),
    session: Session = Depends(get_session),
) -> CicloOut:
    if not TUNEL_RE.match(datos.tunel):
        raise HTTPException(status_code=422, detail="tunel no valido")
    if _ciclo_activo(session, datos.tunel) is not None:
        raise HTTPException(status_code=409, detail="el túnel ya tiene un ciclo activo")
    ciclo = Ciclo(tunel=datos.tunel)
    session.add(ciclo)
    session.commit()
    session.refresh(ciclo)
    return _salida(ciclo)


@router.post("/ciclos/{ciclo_id}/cierre", response_model=CicloOut)
def cerrar_ciclo(
    ciclo_id: int,
    _=Depends(dispositivo_autenticado),
    session: Session = Depends(get_session),
) -> CicloOut:
    ciclo = session.get(Ciclo, ciclo_id)
    if ciclo is None:
        raise HTTPException(status_code=404, detail="ciclo no encontrado")
    if ciclo.terminado_utc is not None:
        raise HTTPException(status_code=409, detail="el ciclo ya está cerrado")
    ciclo.terminado_utc = datetime.now(timezone.utc)
    session.commit()
    session.refresh(ciclo)
    return _salida(ciclo)


@router.post("/ciclos/{ciclo_id}/asignaciones", status_code=201)
def asignar_posiciones(
    ciclo_id: int,
    datos: AsignacionesIn,
    _=Depends(dispositivo_autenticado),
    session: Session = Depends(get_session),
) -> dict:
    ciclo = session.get(Ciclo, ciclo_id)
    if ciclo is None:
        raise HTTPException(status_code=404, detail="ciclo no encontrado")
    if ciclo.terminado_utc is not None:
        raise HTTPException(status_code=409, detail="el ciclo ya está cerrado")
    for asignacion in datos.asignaciones:
        if asignacion.posicion not in POSICIONES_PALLET:
            raise HTTPException(
                status_code=422, detail=f"posicion no valida: {asignacion.posicion}"
            )
    session.add_all(
        AsignacionPosicion(ciclo_id=ciclo_id, posicion=a.posicion, folio=a.folio)
        for a in datos.asignaciones
    )
    try:
        session.commit()
    except IntegrityError:
        session.rollback()
        raise HTTPException(
            status_code=409, detail="posición o folio ya asignado en este ciclo"
        )
    return {"asignadas": len(datos.asignaciones)}
