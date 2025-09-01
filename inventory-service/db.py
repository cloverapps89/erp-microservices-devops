import os
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

#DATABASE_URL = "sqlite+aiosqlite:///./inventory.db"
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "inventory.db")

engine = create_async_engine(f"sqlite+aiosqlite:///{DB_PATH}", connect_args={"check_same_thread": False})

#engine = create_async_engine(DATABASE_URL, echo=True)
SessionLocal = sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)
