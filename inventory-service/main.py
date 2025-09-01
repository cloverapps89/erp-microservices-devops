import os
from contextlib import asynccontextmanager
from typing import List

from fastapi import FastAPI, HTTPException, Request, Depends, Query
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from db import engine, SessionLocal
from models import Base, InventoryItem

# ---------------------------
# Lifespan
# ---------------------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield

app = FastAPI(lifespan=lifespan)
templates = Jinja2Templates(directory="templates")

# ---------------------------
# DB Session Dependency
# ---------------------------
async def get_session() -> AsyncSession:
    async with SessionLocal() as session:
        yield session

# ---------------------------
# Service URLs
# ---------------------------
ORDERS_URL = os.getenv("ORDERS_URL", "http://orders-service:8001")
INVENTORY_URL = os.getenv("INVENTORY_URL", "http://inventory-service:8000")
PUBLIC_ORDERS_URL = os.getenv("PUBLIC_ORDERS_URL", "http://127.0.0.1:8001")
PUBLIC_INVENTORY_URL = os.getenv("PUBLIC_INVENTORY_URL", "http://127.0.0.1:8000")

# ---------------------------
# Routes
# ---------------------------
@app.get("/", response_class=HTMLResponse)
def index(request: Request):
    """Landing page with links to orders and inventory dashboards."""
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "orders": PUBLIC_ORDERS_URL,
            "inventory": PUBLIC_INVENTORY_URL
        }
    )

@app.get("/inventory")
async def get_inventory(
    request: Request,
    session: AsyncSession = Depends(get_session),
    highlight: str = Query(None, description="Comma-separated SKUs to highlight")
):
    """
    Returns inventory as JSON or renders the HTML dashboard.
    Supports optional ?highlight=SKU1,SKU2 for visual emphasis.
    """
    result = await session.execute(select(InventoryItem))
    items: List[InventoryItem] = result.scalars().all()

    # API mode
    if "application/json" in request.headers.get("accept", "").lower():
        inventory_data = [
            {
                "id": item.id,
                "name": item.name,
                "sku": item.sku,
                "quantity": item.quantity,
                "price": item.price,
                "emoji": item.emoji
            }
            for item in items
        ]
        return JSONResponse(content={"inventory": inventory_data})

    # HTML mode
    highlight_skus = highlight.split(",") if highlight else []
    return templates.TemplateResponse(
        "inventory.html",
        {
            "request": request,
            "inventory": items,
            "highlight_skus": highlight_skus
        }
    )

@app.patch("/api/inventory/{sku}")
async def update_inventory(
    sku: str,
    quantity_delta: int,
    session: AsyncSession = Depends(get_session)
):
    """
    Adjusts inventory quantity for a given SKU.
    Returns the new quantity after update.
    """
    result = await session.execute(
        select(InventoryItem).where(InventoryItem.sku == sku)
    )
    item = result.scalar_one_or_none()

    if not item:
        raise HTTPException(status_code=404, detail="Item not found")

    if item.quantity + quantity_delta < 0:
        raise HTTPException(status_code=400, detail="Insufficient stock")

    item.quantity += quantity_delta
    await session.commit()
    await session.refresh(item)

    return {"sku": item.sku, "new_quantity": item.quantity}
