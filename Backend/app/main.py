import os
import logfire
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pathlib import Path

from app.core.log import logger  # noqa: F401
from app.core.config import settings
from app.db.database import async_engine, Base
from app.api.main import api_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create data dir if does not exist
    os.makedirs(settings.data_dir, exist_ok=True)

    # Startup: create all tables
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield

    # Shutdown: dispose the async engine
    await async_engine.dispose()


app = FastAPI(title=settings.project_name, lifespan=lifespan)

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
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)
