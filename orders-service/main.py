import os
import asyncio
import json
from contextlib import asynccontextmanager
from typing import AsyncGenerator, List, Dict, Any

from fastapi import APIRouter, FastAPI, Request, Depends, HTTPException, Query
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse, StreamingResponse
from fastapi.templating import Jinja2Templates

from sqlalchemy import select
from sqlalchemy.orm import selectinload, sessionmaker
from sqlalchemy.ext.asyncio import AsyncSession

import httpx
from dotenv import load_dotenv

from db import engine
from models import Base, Customer, OrderItem, OrderInventoryLink

from health import router as health_router

# ---------------------------
# Setup
# ---------------------------

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "templates"))

load_dotenv()
INVENTORY_URL = os.getenv("INVENTORY_URL")

SessionLocal = sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False
)

# ---------------------------
# Lifespan
# ---------------------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield

app = FastAPI(lifespan=lifespan)
app.include_router(health_router)
# ---------------------------
# DB Session Dependency
# ---------------------------
async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async with SessionLocal() as session:
        yield session

# ---------------------------
# SSE Support
# ---------------------------
subscribers: list[asyncio.Queue] = []

async def event_generator(queue: asyncio.Queue):
    try:
        while True:
            data = await queue.get()
            yield f"data: {data}\n\n"
    except asyncio.CancelledError:
        pass

@app.get("/orders/stream")
async def orders_stream():
    queue: asyncio.Queue = asyncio.Queue()
    subscribers.append(queue)

    async def streamer():
        try:
            async for chunk in event_generator(queue):
                yield chunk
        finally:
            if queue in subscribers:
                subscribers.remove(queue)

    return StreamingResponse(streamer(), media_type="text/event-stream")

def broadcast_event(message: str):
    for queue in list(subscribers):
        try:
            queue.put_nowait(message)
        except asyncio.QueueFull:
            pass

# ---------------------------
# Inventory Helpers
# ---------------------------
async def fetch_inventory():
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get(f"{INVENTORY_URL}/inventory",
                                    headers={"Accept": "application/json"})
            resp.raise_for_status()
            data = resp.json()
            return data.get("inventory", []), None
    except httpx.HTTPStatusError as e:
        return [], f"Inventory responded with {e.response.status_code}"
    except httpx.RequestError as e:
        return [], f"Could not reach inventory: {str(e)}"

async def validate_stock(items_data: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    inventory, error = await fetch_inventory()
    if error:
        raise HTTPException(status_code=503, detail=error)

    sku_lookup = {item["sku"]: item for item in inventory}

    for item in items_data:
        sku = item.get("sku")
        qty = item.get("quantity", 0)
        if not sku or qty <= 0:
            raise HTTPException(status_code=400, detail=f"Invalid item entry: {item}")
        inv_item = sku_lookup.get(sku)
        if not inv_item:
            raise HTTPException(status_code=404, detail=f"SKU {sku} not found in inventory")
        if inv_item["quantity"] < qty:
            raise HTTPException(status_code=400, detail=f"Insufficient stock for {sku}")

    return sku_lookup

async def decrement_inventory(items: List[Dict[str, Any]]) -> Dict[str, int]:
    updated_stock = {}
    async with httpx.AsyncClient(timeout=5.0) as client:
        for link in items:
            resp = await client.patch(
                f"{INVENTORY_URL}/api/inventory/{link['sku']}",
                params={"quantity_delta": -link["quantity"]}
            )
            if resp.status_code != 200:
                raise HTTPException(
                    status_code=400,
                    detail=f"Inventory update failed for {link['sku']}: {resp.text}"
                )
            data = resp.json()
            updated_stock[data["sku"]] = data["new_quantity"]
    return updated_stock

# ---------------------------
# Routes
# ---------------------------
@app.post("/orders")
async def create_order(
    request: Request,
    session: AsyncSession = Depends(get_session)
):
    data = await request.json()
    order_number = data.get("order_number")
    customer_id = data.get("customer_id")
    customer_name = data.get("customer_name")
    customer_nickname = data.get("customer_nickname")
    customer_email = data.get("customer_email")
    items_data = data.get("items", [])

    if not order_number or not items_data:
        raise HTTPException(status_code=400, detail="Order number and items are required")

    if not customer_id and not all([customer_name, customer_nickname, customer_email]):
        raise HTTPException(
            status_code=400,
            detail="Either customer_id or customer_name, customer_nickname, and customer_email are required"
        )

    sku_lookup = await validate_stock(items_data)

    # Ensure customer exists or create one
    customer_obj = None
    if customer_id:
        result = await session.execute(
            select(Customer).where(Customer.id == customer_id)
        )
        customer_obj = result.scalar_one_or_none()

    if not customer_obj and (customer_nickname or customer_email):
        stmt = select(Customer)
        if customer_nickname and customer_email:
            stmt = stmt.where(
                (Customer.nickname == customer_nickname) | (Customer.email == customer_email)
            )
        elif customer_nickname:
            stmt = stmt.where(Customer.nickname == customer_nickname)
        elif customer_email:
            stmt = stmt.where(Customer.email == customer_email)

        result = await session.execute(stmt)
        customer_obj = result.scalar_one_or_none()

    if not customer_obj:
        customer_obj = Customer(
            name=customer_name,
            nickname=customer_nickname,
            email=customer_email
        )
        session.add(customer_obj)
        await session.flush()

    # Build order
    order_links = [
        OrderInventoryLink(
            sku=item["sku"],
            quantity=item["quantity"],
            price_at_order=item.get("price", 0)
        )
        for item in items_data
    ]

    order_links_data = [
        {"sku": item["sku"], "quantity": item["quantity"]}
        for item in items_data
    ]

    order = OrderItem(
        order_number=order_number,
        customer_id=customer_obj.id,
        items=order_links
    )
    session.add(order)
    await session.commit()

    # Reload order with customer
    result = await session.execute(
        select(OrderItem)
        .options(selectinload(OrderItem.customer))
        .where(OrderItem.id == order.id)
    )
    order = result.scalar_one()

    # Decrement inventory
    try:
        updated_stock = await decrement_inventory(order_links_data)
    except HTTPException as e:
        await session.delete(order)
        await session.commit()
        raise e

    # Fetch inventory to enrich order items with names/emojis
    inventory, _ = await fetch_inventory()
    sku_lookup = {item["sku"]: item for item in inventory}

# Broadcast SSE event only after successful inventory update
    broadcast_event(json.dumps({
    "id": order.id,
    "order_number": order.order_number,
    "customer": {
        "name": order.customer.name,
        "nickname": order.customer.nickname,
        "email": order.customer.email
    },
    "created_at": order.created_at.isoformat() if order.created_at else None,
    "items": [
        {
            "sku": link.sku,
            "name": sku_lookup.get(link.sku, {}).get("name"),
            "emoji": sku_lookup.get(link.sku, {}).get("emoji"),
            "quantity": link.quantity,
            "price": link.price_at_order,
            "new_quantity": updated_stock.get(link.sku)
        }
        for link in order.items
    ],
    "highlight_skus": list(updated_stock.keys())
}))

    if "text/html" in request.headers.get("accept", "").lower():
        highlight_skus = ",".join(updated_stock.keys())
        return RedirectResponse(
            url=f"/orders-with-inventory?highlight={highlight_skus}",
            status_code=303
        )

    return {
        "message": "Order created",
        "order_id": order.id,
        "customer": {
            "name": order.customer.name,
            "nickname": order.customer.nickname,
            "email": order.customer.email
        },
        "updated_stock": updated_stock,
        "highlight_skus": list(updated_stock.keys())
    }

@app.get("/orders-with-inventory")
async def orders_with_inventory(
    request: Request,
    session: AsyncSession = Depends(get_session),
    format: str = Query("html", enum=["html", "json"]),
    highlight: str = Query(None)
):
    inventory, error = await fetch_inventory()
    sku_lookup = {item["sku"]: item for item in inventory}

    result = await session.execute(
        select(OrderItem)
        .options(
            selectinload(OrderItem.customer),
            selectinload(OrderItem.items)
        )
        .order_by(OrderItem.created_at.desc())
    )
    orders = result.unique().scalars().all()

    serialized_orders = [
        {
            "order_number": order.order_number,
            "customer": order.customer.nickname if order.customer else None,
            "created_at": order.created_at.strftime("%Y-%m-%d") if order.created_at else None,
            "items": [
                {
                    "sku": link.sku,
                    "name": sku_lookup.get(link.sku, {}).get("name"),
                    "emoji": sku_lookup.get(link.sku, {}).get("emoji"),
                    "quantity": link.quantity,
                    "price": link.price_at_order
                }
                for link in (order.items or [])
            ]
        }
        for order in orders
    ]

    highlight_list = highlight.split(",") if highlight else []

    if format == "json":
        return JSONResponse(content={
            "orders": serialized_orders,
            "inventory": inventory,
            "error": error,
            "highlight_skus": highlight_list
        })

    return templates.TemplateResponse("index.html", {
        "request": request,
        "orders": serialized_orders,
        "inventory": inventory,
        "error": error,
        "highlight_skus": highlight_list
    })