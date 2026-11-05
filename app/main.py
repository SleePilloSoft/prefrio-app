from fastapi import FastAPI
from fastapi.responses import JSONResponse
from sqlalchemy import text

from app.db import engine

app = FastAPI(title="Prefrío API", version="0.1.0")


@app.get("/health")
def health():
    try:
        with engine.connect() as conexion:
            conexion.execute(text("SELECT 1"))
    except Exception:
        return JSONResponse({"status": "error", "db": "no disponible"}, status_code=503)
    return {"status": "ok", "db": "ok"}
