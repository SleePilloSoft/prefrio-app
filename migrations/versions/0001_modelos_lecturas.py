"""modelos base de lecturas

Revision ID: 0001
Revises:
Create Date: 2026-11-05
"""

import sqlalchemy as sa
from alembic import op

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "ciclos",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("tunel", sa.String(64), nullable=False),
        sa.Column("iniciado_utc", sa.DateTime(timezone=True), nullable=False),
        sa.Column("terminado_utc", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_ciclos_tunel", "ciclos", ["tunel"])

    op.create_table(
        "sensores",
        sa.Column("sensor_id", sa.String(64), primary_key=True),
        sa.Column("tipo", sa.String(16), nullable=False),
        sa.Column("tunel", sa.String(64), nullable=False),
        sa.Column("posicion", sa.String(8), nullable=True),
    )
    op.create_index("ix_sensores_tunel", "sensores", ["tunel"])

    op.create_table(
        "asignaciones_posicion",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("ciclo_id", sa.Integer(), sa.ForeignKey("ciclos.id"), nullable=False),
        sa.Column("posicion", sa.String(8), nullable=False),
        sa.Column("folio", sa.String(64), nullable=False),
        sa.UniqueConstraint("ciclo_id", "posicion", name="uq_asignacion_ciclo_posicion"),
        sa.UniqueConstraint("ciclo_id", "folio", name="uq_asignacion_ciclo_folio"),
    )
    op.create_index("ix_asignaciones_posicion_ciclo_id", "asignaciones_posicion", ["ciclo_id"])

    op.create_table(
        "lecturas",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("dispositivo", sa.String(64), nullable=False),
        sa.Column("id_local", sa.Integer(), nullable=False),
        sa.Column("sensor_id", sa.String(64), nullable=False),
        sa.Column("tipo", sa.String(16), nullable=False),
        sa.Column("tunel", sa.String(64), nullable=False),
        sa.Column("posicion", sa.String(8), nullable=True),
        sa.Column("fecha_utc", sa.DateTime(timezone=True), nullable=False),
        sa.Column("temperatura", sa.Float(), nullable=True),
        sa.Column("humedad", sa.Float(), nullable=True),
        sa.Column("recibido_utc", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("dispositivo", "id_local", name="uq_lectura_dispositivo_id_local"),
    )
    op.create_index("ix_lecturas_sensor_id", "lecturas", ["sensor_id"])
    op.create_index("ix_lecturas_tunel", "lecturas", ["tunel"])


def downgrade():
    op.drop_index("ix_lecturas_tunel", table_name="lecturas")
    op.drop_index("ix_lecturas_sensor_id", table_name="lecturas")
    op.drop_table("lecturas")
    op.drop_index("ix_asignaciones_posicion_ciclo_id", table_name="asignaciones_posicion")
    op.drop_table("asignaciones_posicion")
    op.drop_index("ix_sensores_tunel", table_name="sensores")
    op.drop_table("sensores")
    op.drop_index("ix_ciclos_tunel", table_name="ciclos")
    op.drop_table("ciclos")
