from fastapi import FastAPI
from contextlib import asynccontextmanager
from db import engine
from models import Base
from health import router as health_router
from routers import inventory

# ---------------------------
# Lifespan
# ---------------------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield


# ---------------------------
# App setup
# ---------------------------
app = FastAPI(lifespan=lifespan)

# Routers
app.include_router(health_router)
app.include_router(inventory.router, prefix="/inventory", tags=["inventory"])