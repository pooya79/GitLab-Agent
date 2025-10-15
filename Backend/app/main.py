from dotenv import load_dotenv
import os

import logfire
from sqlalchemy import select
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pathlib import Path

from core.log import logger
from db.models import User
from core.config import settings
from db.database import async_engine, Base, AsyncSessionLocal
from core.security import hash_password
from api.main import api_router

load_dotenv()

# Setup logfire for monitoring
if settings.logfire_token:
    logfire.configure(token=settings.logfire_token)
    logfire.instrument_pydantic_ai()
    logfire.instrument_fastapi()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create data dir if does not exist
    os.makedirs(settings.data_dir, exist_ok=True)

    # Startup: create all tables
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with AsyncSessionLocal() as session:
        # look up by username (or email)
        existing = await session.execute(
            select(User).where(User.username == settings.admin_username)
        )
        if not existing.scalars().first():
            admin = User(
                username=settings.admin_username,
                email=settings.admin_email,
                hashed_password=hash_password(settings.admin_password),
            )
            session.add(admin)
            await session.commit()

            logger.info(f"Created admin user '{settings.admin_username}'")
    yield

    # Shutdown: dispose the async engine
    await async_engine.dispose()


app = FastAPI(title=settings.project_name, lifespan=lifespan)

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
