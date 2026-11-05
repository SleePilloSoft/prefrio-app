from datetime import datetime, timezone

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


def ahora_utc() -> datetime:
    return datetime.now(timezone.utc)


class Dispositivo(Base):
    """Tablero (Raspberry) autorizado a enviar lecturas. Guarda solo el hash del token."""

    __tablename__ = "dispositivos"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    nombre: Mapped[str] = mapped_column(String(64), unique=True)
    token_hash: Mapped[str] = mapped_column(String(64), unique=True)
    creado_utc: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=ahora_utc)
    revocado_utc: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class Ciclo(Base):
    """Carga y pre-frío de un túnel. Se completa en la fase de ciclo."""

    __tablename__ = "ciclos"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    tunel: Mapped[str] = mapped_column(String(64), index=True)
    iniciado_utc: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=ahora_utc)
    terminado_utc: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class Sensor(Base):
    """Sonda DS18B20 (con posición) o sensor SHT30 del túnel (posición TUNEL)."""

    __tablename__ = "sensores"

    sensor_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    tipo: Mapped[str] = mapped_column(String(16))
    tunel: Mapped[str] = mapped_column(String(64), index=True)
    posicion: Mapped[str | None] = mapped_column(String(8), nullable=True)


class AsignacionPosicion(Base):
    """Posición del túnel asociada a un folio, por ciclo."""

    __tablename__ = "asignaciones_posicion"
    __table_args__ = (
        UniqueConstraint("ciclo_id", "posicion", name="uq_asignacion_ciclo_posicion"),
        UniqueConstraint("ciclo_id", "folio", name="uq_asignacion_ciclo_folio"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    ciclo_id: Mapped[int] = mapped_column(ForeignKey("ciclos.id"), index=True)
    posicion: Mapped[str] = mapped_column(String(8))
    folio: Mapped[str] = mapped_column(String(64))


class Lectura(Base):
    """Lectura enviada por un tablero (Raspberry). Idempotente por dispositivo + id_local."""

    __tablename__ = "lecturas"
    __table_args__ = (
        UniqueConstraint("dispositivo", "id_local", name="uq_lectura_dispositivo_id_local"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    dispositivo: Mapped[str] = mapped_column(String(64))
    id_local: Mapped[int] = mapped_column(Integer)
    sensor_id: Mapped[str] = mapped_column(String(64), index=True)
    tipo: Mapped[str] = mapped_column(String(16))
    tunel: Mapped[str] = mapped_column(String(64), index=True)
    posicion: Mapped[str | None] = mapped_column(String(8), nullable=True)
    fecha_utc: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    temperatura: Mapped[float | None] = mapped_column(Float, nullable=True)
    humedad: Mapped[float | None] = mapped_column(Float, nullable=True)
    recibido_utc: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=ahora_utc)
