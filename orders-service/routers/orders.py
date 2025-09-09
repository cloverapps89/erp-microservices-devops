from datetime import datetime
import json
import os
from fastapi import APIRouter, Request, Depends, HTTPException, Query
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from db import get_session
from models import Customer, OrderItem, OrderInventoryLink
from sse import broadcast_event
from inventory_client import fetch_inventory, validate_stock, decrement_inventory

from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
TEMPLATES_DIR = PROJECT_ROOT  / "templates"
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

router = APIRouter()

# Check root
ORDERS_URL = os.getenv("ORDERS_URL", "http://orders-service:8002")

@router.get("")
async def orders(
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

    return templates.TemplateResponse("order.html", {"request": request, "orders": serialized_orders, "inventory": inventory, "error": error, "highlight_skus": highlight_list})
  

@router.post("")
async def create_orders(request: Request, session: AsyncSession = Depends(get_session)):
    data = await request.json()

    # Normalize input: wrap single dict into a list
    if isinstance(data, dict):
        orders_data = [data]
    elif isinstance(data, list):
        orders_data = data
    else:
        raise HTTPException(status_code=400, detail="Invalid payload format. Must be an object or a list.")

    results = []
    updated_stock = {}

    try:
        for order_data in orders_data:
            order_number = order_data.get("order_number")
            customer_id = order_data.get("customer_id")
            customer_name = order_data.get("customer_name")
            customer_nickname = order_data.get("customer_nickname")
            customer_email = order_data.get("customer_email")
            items_data = order_data.get("items", [])

            if not order_number or not items_data:
                results.append({
                    "order_number": order_number,
                    "status": "failed",
                    "reason": "Order number and items are required"
                })
                continue

            # ✅ Validate stock before creating
            await validate_stock(items_data)

            # Ensure customer exists or create
            customer_obj = None
            if customer_id:
                result = await session.execute(select(Customer).where(Customer.id == customer_id))
                customer_obj = result.scalar_one_or_none()

            if not customer_obj:
                customer_obj = Customer(
                    name=customer_name,
                    nickname=customer_nickname,
                    email=customer_email
                )
                session.add(customer_obj)
                await session.flush()

            # Build order + links
            order_links = [
                OrderInventoryLink(
                    sku=item["sku"],
                    quantity=item["quantity"],
                    price_at_order=item.get("price", 0)
                )
                for item in items_data
            ]
            order_links_data = [{"sku": item["sku"], "quantity": item["quantity"], "price": item.get("price", 0)} for item in items_data]

            order = OrderItem(order_number=order_number, customer_id=customer_obj.id, items=order_links)
            session.add(order)

            # Flush so we get order.id
            await session.flush()

            # Update inventory
            updated_stock_for_order = await decrement_inventory(order_links_data)
            updated_stock.update(updated_stock_for_order)

            # Reload order with customer
            result = await session.execute(
                select(OrderItem).options(selectinload(OrderItem.customer)).where(OrderItem.id == order.id)
            )
            order = result.scalar_one()

            results.append({
                "order_number": order.order_number,
                "status": "success",
                "order_id": order.id,
                "customer": {
                    "name": order.customer.name,
                    "nickname": order.customer.nickname,
                    "email": order.customer.email
                },
                "items": order_links_data,
                "updated_stock": updated_stock_for_order
            })

        # Commit all orders in one DB transaction
        await session.commit()

    except Exception as e:
        await session.rollback()
        raise HTTPException(status_code=500, detail=f"Error creating orders: {str(e)}")

    # 🔄 Broadcast each order individually so frontend keeps working
    inventory, _ = await fetch_inventory()
    sku_lookup = {item["sku"]: item for item in inventory}

    for result in results:
        if result["status"] != "success":
            continue

        broadcast_event(json.dumps({
            "order_number": result["order_number"],
            "customer": result["customer"],
            "created_at": datetime.utcnow().isoformat(),
            "items": [
                {
                    "sku": item["sku"],
                    "name": sku_lookup.get(item["sku"], {}).get("name"),
                    "emoji": sku_lookup.get(item["sku"], {}).get("emoji"),
                    "quantity": item["quantity"],
                    "price": item["price"],
                    "new_quantity": result["updated_stock"].get(item["sku"])
                }
                for item in result["items"]
            ],
            "highlight_skus": list(result["updated_stock"].keys())
        }))

    return {"message": "Batch processed", "results": results, "updated_stock": updated_stock}


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
