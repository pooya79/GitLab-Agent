import os
import logfire
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pathlib import Path

from app.core.log import logger  # noqa: F401
from app.core.config import settings
from app.db.database import init_db, close_client
from app.api.main import api_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create data dir if does not exist
    os.makedirs(settings.data_dir, exist_ok=True)

    # Startup: ensure indexes exist
    init_db()
    yield

    # Shutdown: close the Mongo client
    close_client()


app = FastAPI(title=settings.project_name, lifespan=lifespan, docs_url="/api/docs", openapi_url="/api/openapi.json")

# Setup logfire for monitoring
if settings.logfire_token:
    logfire.configure(token=settings.logfire_token)
    logfire.instrument_pydantic_ai()
    logfire.instrument_fastapi(app, capture_headers=True)

ASSETS_DIR = Path(__file__).resolve().parent / "assets"
AVATARS_DIR = ASSETS_DIR / "avatars"
AVATARS_URL_PREFIX = "/api/static/avatars"

app.mount(AVATARS_URL_PREFIX, StaticFiles(directory=str(AVATARS_DIR)), name="avatars")

origins = [
    "http://localhost:3000",
    settings.frontend_url,
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)
