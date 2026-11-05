from datetime import datetime

from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.models import AsignacionPosicion, Ciclo


def folio_para(session: Session, tunel: str, posicion: str | None, fecha_utc: datetime) -> str | None:
    """Folio que estaba en la posición del túnel en el momento de la lectura.

    Se calcula al consultar, no al recibir: así una corrección de asignación
    se refleja también en lecturas anteriores, sin perder datos.
    Devuelve None si la sonda no tiene posición de pallet, si no hay ciclo
    activo en esa fecha o si la posición no tiene folio asignado.
    """
    if posicion is None or posicion == "TUNEL":
        return None
    ciclo = session.scalar(
        select(Ciclo)
        .where(
            Ciclo.tunel == tunel,
            Ciclo.iniciado_utc <= fecha_utc,
            or_(Ciclo.terminado_utc.is_(None), Ciclo.terminado_utc > fecha_utc),
        )
        .order_by(Ciclo.iniciado_utc.desc())
    )
    if ciclo is None:
        return None
    return session.scalar(
        select(AsignacionPosicion.folio).where(
            AsignacionPosicion.ciclo_id == ciclo.id,
            AsignacionPosicion.posicion == posicion,
        )
    )
