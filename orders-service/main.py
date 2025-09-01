import os
from fastapi import FastAPI
from contextlib import asynccontextmanager
from fastapi.templating import Jinja2Templates
from db import engine
from models import Base
from health import router as health_router
from routers import orders
from sse import router as sse_router

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "templates"))
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
app.include_router(orders.router, prefix="/orders", tags=["orders"])
app.include_router(sse_router, prefix="/orders", tags=["orders-stream"])
