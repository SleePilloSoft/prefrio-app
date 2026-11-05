from alembic import context

import app.models  # noqa: F401  (registra las tablas en Base.metadata)
from app.db import Base, engine

target_metadata = Base.metadata


def run_migrations_online():
    with engine.connect() as conexion:
        context.configure(connection=conexion, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()


run_migrations_online()
