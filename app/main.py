import logging
from contextlib import asynccontextmanager

from fastapi import APIRouter, FastAPI, Request
from fastapi.responses import JSONResponse
from sqlalchemy import text

from app.database import Base, SessionLocal, engine
from app.ingestion import ingest
from app.routers import aggregates, patterns

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    with engine.begin() as conn:
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS postgis"))
    Base.metadata.create_all(engine)
    logger.info("Database connection established, schema ready")

    with SessionLocal() as session:
        ingest(session)

    yield


app = FastAPI(lifespan=lifespan)


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    logger.exception("Unhandled exception")
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})


@app.get("/health")
async def health():
    return {"status": "ok"}


api_router = APIRouter(prefix="/api/v1")
api_router.include_router(aggregates.router, prefix="/aggregates", tags=["aggregates"])
api_router.include_router(patterns.router, prefix="/patterns", tags=["patterns"])
app.include_router(api_router)
