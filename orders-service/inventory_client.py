import httpx
import os
from fastapi import HTTPException
from typing import List, Dict, Any

INVENTORY_URL = os.getenv("INVENTORY_URL", "http://inventory-service:8000")


async def fetch_inventory():
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get(f"{INVENTORY_URL}/inventory", headers={"Accept": "application/json"})
            resp.raise_for_status()
            data = resp.json()
            return data.get("inventory", []), None
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
