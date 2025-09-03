import os
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base

# Use env var or fallback
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///data/inventory.db")

engine = create_async_engine("sqlite+aiosqlite:////data/inventory.db", connect_args={"check_same_thread": False})

SessionLocal = sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)
print("Resolved DB path:", DATABASE_URL)
print("Current working directory:", os.getcwd())
Base = declarative_base()