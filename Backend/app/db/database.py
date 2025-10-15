from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base
from app.core.config import settings
import app.db.models  # noqa: F401

# Database URL — adjust for your environment
SQLALCHEMY_DATABASE_URL = settings.sqlite.url

# Create an async engine
async_engine = create_async_engine(
    SQLALCHEMY_DATABASE_URL,
    echo=True,  # logs SQL for debugging
)

# Configure a sessionmaker for AsyncSession
AsyncSessionLocal = sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    expire_on_commit=False,  # optional, so objects don’t expire on you
)

# Base class for models
Base = declarative_base()
