"""tabla de dispositivos con token revocable

Revision ID: 0002
Revises: 0001
Create Date: 2026-11-05
"""

import sqlalchemy as sa
from alembic import op

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "dispositivos",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("nombre", sa.String(64), nullable=False),
        sa.Column("token_hash", sa.String(64), nullable=False),
        sa.Column("creado_utc", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revocado_utc", sa.DateTime(timezone=True), nullable=True),
        sa.UniqueConstraint("nombre", name="uq_dispositivo_nombre"),
        sa.UniqueConstraint("token_hash", name="uq_dispositivo_token_hash"),
    )


def downgrade():
    op.drop_table("dispositivos")
