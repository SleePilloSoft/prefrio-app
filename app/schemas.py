from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

POSICIONES_VALIDAS = {f"A{i}" for i in range(1, 11)} | {f"B{i}" for i in range(1, 11)} | {"TUNEL"}


class LecturaIn(BaseModel):
    id_local: int
    fecha_utc: datetime
    sensor_id: str = Field(min_length=1, max_length=64)
    tipo: Literal["ds18b20", "sht30"]
    posicion: str | None = Field(default=None, max_length=8)
    temperatura: float | None = None
    humedad: float | None = None


class LoteIn(BaseModel):
    dispositivo: str = Field(min_length=1, max_length=64)
    tunel: str = Field(min_length=1, max_length=64)
    lecturas: list[LecturaIn] = Field(max_length=500)


class RechazoOut(BaseModel):
    id_local: int
    motivo: str


class RespuestaOut(BaseModel):
    aceptadas: list[int]
    duplicadas: list[int]
    rechazadas: list[RechazoOut]
