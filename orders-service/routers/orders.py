import json
from fastapi import APIRouter, Request, Depends, HTTPException, Query
from fastapi.responses import RedirectResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from db import get_session
from models import Customer, OrderItem, OrderInventoryLink
from sse import broadcast_event
from inventory_client import fetch_inventory, validate_stock, decrement_inventory

templates = Jinja2Templates(directory="templates")
router = APIRouter()


@router.post("")
async def create_order(request: Request, session: AsyncSession = Depends(get_session)):
    data = await request.json()
    order_number = data.get("order_number")
    customer_id = data.get("customer_id")
    customer_name = data.get("customer_name")
    customer_nickname = data.get("customer_nickname")
    customer_email = data.get("customer_email")
    items_data = data.get("items", [])

    if not order_number or not items_data:
        raise HTTPException(status_code=400, detail="Order number and items are required")

    sku_lookup = await validate_stock(items_data)

    # Ensure customer exists or create
    customer_obj = None
    if customer_id:
        result = await session.execute(select(Customer).where(Customer.id == customer_id))
        customer_obj = result.scalar_one_or_none()

    if not customer_obj:
        customer_obj = Customer(name=customer_name, nickname=customer_nickname, email=customer_email)
        session.add(customer_obj)
        await session.flush()

    order_links = [OrderInventoryLink(sku=item["sku"], quantity=item["quantity"], price_at_order=item.get("price", 0))
                   for item in items_data]
    order_links_data = [{"sku": item["sku"], "quantity": item["quantity"]} for item in items_data]

    order = OrderItem(order_number=order_number, customer_id=customer_obj.id, items=order_links)
    session.add(order)
    await session.commit()

    # Reload order
    result = await session.execute(select(OrderItem).options(selectinload(OrderItem.customer)).where(OrderItem.id == order.id))
    order = result.scalar_one()

    # Update inventory
    updated_stock = await decrement_inventory(order_links_data)

    inventory, _ = await fetch_inventory()
    sku_lookup = {item["sku"]: item for item in inventory}

    # Broadcast event
    broadcast_event(json.dumps({
        "order_number": order.order_number,
        "customer": {"name": order.customer.name, "nickname": order.customer.nickname, "email": order.customer.email},
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
        return RedirectResponse(url=f"/orders/orders-with-inventory?highlight={highlight_skus}", status_code=303)

    return {"message": "Order created", "order_id": order.id, "updated_stock": updated_stock}


@router.get("/orders-with-inventory")
async def orders_with_inventory(
    request: Request,
    session: AsyncSession = Depends(get_session),
    format: str = Query("html", enum=["html", "json"]),
    highlight: str = Query(None)
):
    inventory, error = await fetch_inventory()
    sku_lookup = {item["sku"]: item for item in inventory}

    result = await session.execute(select(OrderItem).options(selectinload(OrderItem.customer), selectinload(OrderItem.items)).order_by(OrderItem.created_at.desc()))
    orders = result.unique().scalars().all()

    serialized_orders = [
        {
            "order_number": order.order_number,
            "customer": order.customer.nickname if order.customer else None,
            "created_at": order.created_at.strftime("%Y-%m-%d") if order.created_at else None,
            "items": [
                {"sku": link.sku, "name": sku_lookup.get(link.sku, {}).get("name"), "emoji": sku_lookup.get(link.sku, {}).get("emoji"), "quantity": link.quantity, "price": link.price_at_order}
                for link in (order.items or [])
            ]
        }
        for order in orders
    ]

    highlight_list = highlight.split(",") if highlight else []

    if format == "json":
        return JSONResponse(content={"orders": serialized_orders, "inventory": inventory, "error": error, "highlight_skus": highlight_list})

    return templates.TemplateResponse("index.html", {"request": request, "orders": serialized_orders, "inventory": inventory, "error": error, "highlight_skus": highlight_list})
