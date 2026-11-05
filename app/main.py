from fastapi import FastAPI
from fastapi.responses import JSONResponse
from sqlalchemy import text

from app.db import engine
from app.routers import ciclos, lecturas

app = FastAPI(title="Prefrío API", version="0.1.0")
app.include_router(lecturas.router, prefix="/api/v1")
app.include_router(ciclos.router, prefix="/api/v1")


@app.get("/health")
def health():
    try:
        with engine.connect() as conexion:
            conexion.execute(text("SELECT 1"))
    except Exception:
        return JSONResponse({"status": "error", "db": "no disponible"}, status_code=503)
    return {"status": "ok", "db": "ok"}
