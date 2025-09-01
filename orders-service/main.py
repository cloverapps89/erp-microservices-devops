import os
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, Request, Depends
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates

from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

import httpx

from db import engine, SessionLocal
from models import Base, OrderItem
from serializers import serialize_order

# 🧩 Templating setup
templates = Jinja2Templates(directory="templates")

# 🔗 External service URL
INVENTORY_URL = os.getenv("INVENTORY_URL", "http://inventory-service:8000")

# 🌱 App lifecycle
@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield

# 🚀 FastAPI app
app = FastAPI(lifespan=lifespan)

# 🛠️ DB session dependency
async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async with SessionLocal() as session:
        yield session

# 🔹 Fetch inventory from inventory-service
async def fetch_inventory():
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get(f"{INVENTORY_URL}/api/inventory")
            resp.raise_for_status()
            data = resp.json()
            return data.get("inventory", []), None
    except httpx.HTTPStatusError as e:
        return [], f"Inventory responded with {e.response.status_code}"
    except httpx.RequestError as e:
        return [], f"Could not reach inventory: {str(e)}"

# 🔹 HTML route
@app.get("/orders-with-inventory", response_class=HTMLResponse)
async def orders_with_inventory_html(request: Request, session: AsyncSession = Depends(get_session)):
    inventory, error = await fetch_inventory()

    result = await session.execute(
        select(OrderItem).options(selectinload(OrderItem.customer))  # ✅ eager load
    )
    orders = result.scalars().all()
    serialized_orders = [serialize_order(o) for o in orders]  # safe now

    return templates.TemplateResponse("index.html", {
        "request": request,
        "orders": serialized_orders,
        "inventory": inventory,
        "error": error
    })

# 🔹 API route
@app.get("/api/orders-with-inventory", response_class=JSONResponse)
async def orders_with_inventory_api(session: AsyncSession = Depends(get_session)):
    inventory, error = await fetch_inventory()

    result = await session.execute(
        select(OrderItem).options(selectinload(OrderItem.customer))  # ✅ eager load
    )
    orders = result.scalars().all()
    serialized_orders = [serialize_order(o) for o in orders]

    if error:
        return JSONResponse(content={
            "error": error,
            "orders": [],
            "inventory": []
        })

    return JSONResponse(content={
        "orders": serialized_orders,
        "inventory": inventory
    })
