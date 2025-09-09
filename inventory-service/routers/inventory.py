import os
from pathlib import Path
from typing import List
from fastapi import APIRouter, HTTPException, Request, Depends, Query
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from db import get_session
from models import InventoryItem

PROJECT_ROOT = Path(__file__).resolve().parent.parent
TEMPLATES_DIR = PROJECT_ROOT  / "templates"
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

router = APIRouter()
# ---------------------------
# Service URLs
# ---------------------------
INVENTORY_URL = os.getenv("INVENTORY_URL", "http://inventory-service:8001")
ORDERS_URL = os.getenv("ORDERS_URL", "http://orders-service:8002")
VENDOR_URL = os.getenv("VENDOR_URL", "http://vendor-service:8003")

PUBLIC_INVENTORY_URL = os.getenv("PUBLIC_INVENTORY_URL", "http://127.0.0.1:8001")
PUBLIC_ORDERS_URL = os.getenv("PUBLIC_ORDERS_URL", "http://127.0.0.1:8002")
PUBLIC_VENDOR_URL = os.getenv("PUBLIC_VENDOR_URL","http://127.0.0.1:8003")

# ---------------------------
# Routes
# ---------------------------

@router.get("")
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

@router.patch("/api/inventory/{sku}")
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
