from datetime import datetime

from pydantic import BaseModel, Field


class CicloIn(BaseModel):
    tunel: str = Field(min_length=1, max_length=64)


class CicloOut(BaseModel):
    id: int
    tunel: str
    iniciado_utc: datetime
    terminado_utc: datetime | None


class AsignacionIn(BaseModel):
    posicion: str = Field(min_length=1, max_length=8)
    folio: str = Field(min_length=1, max_length=64)


class AsignacionesIn(BaseModel):
    asignaciones: list[AsignacionIn] = Field(min_length=1, max_length=500)
