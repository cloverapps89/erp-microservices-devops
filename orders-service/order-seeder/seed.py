import asyncio
import os
import random
import string
from datetime import datetime, timezone, timedelta

import httpx

# Config
ORDERS_API = os.getenv("ORDERS_API", "http://localhost:8002/orders")
INVENTORY_API = os.getenv("INVENTORY_API", "http://localhost:8001/inventory")
HTTP_TIMEOUT = float(os.getenv("HTTP_TIMEOUT", 10))


# Sample customers
customer_data = [
    {"name": "Alice Johnson", "nickname": "AJ", "email": "alice.j@example.com"},
    {"name": "Robert Smith", "nickname": "Bobby", "email": "robert.smith@example.com"},
    {"name": "Cynthia Lee", "nickname": "Cyn", "email": "cynthia.lee@example.com"},
]

def random_suffix(length=4):
    return ''.join(random.choices(string.ascii_lowercase + string.digits, k=length))

def random_customer():
    base = random.choice(customer_data)
    suffix = random_suffix()
    return {
        "name": base["name"],
        "nickname": f"{base['nickname']}_{suffix}",
        "email": f"{base['email'].split('@')[0]}_{suffix}@{base['email'].split('@')[1]}",
    }

async def fetch_inventory(client):
    try:
        resp = await client.get(
            INVENTORY_API,
            headers={"Accept": "application/json"},
            timeout=HTTP_TIMEOUT,
        )
        resp.raise_for_status()
        return resp.json().get("inventory", [])
    except Exception as e:
        print(f"❌ Failed to fetch inventory: {e}")
        return []



def generate_order_payload(inventory):
    if not inventory:
        return None
    cust = random_customer()
    items = random.sample(inventory, k=min(len(inventory), random.randint(1, 5)))
    items_payload = [
        {"sku": item["sku"], "quantity": random.randint(1, min(item["quantity"], 10)), "price": item["price"]}
        for item in items if item["quantity"] > 0
    ]
    if not items_payload:
        return None
    return {
        "order_number": f"{int(datetime.now().timestamp())}{random.randint(100,999)}",
        "customer_name": cust["name"],
        "customer_nickname": cust["nickname"],
        "customer_email": cust["email"],
        "items": items_payload,
    }

async def seed_orders(n=10, batch_size=5):
    async with httpx.AsyncClient(timeout=HTTP_TIMEOUT) as client:
        inventory = await fetch_inventory(client)
        print(f"🧪 Started batch - #orders {n} - #perbatch {batch_size}", flush=True)
        if not inventory:
            print("❌ No inventory available.")
            return

        for i in range(0, n, batch_size):
            
            batch = [generate_order_payload(inventory) for _ in range(batch_size)]
            batch = [b for b in batch if b]  # drop Nones
            if not batch:
                continue

            try:
                resp = await client.post(ORDERS_API, json=batch, headers={"Accept": "application/json"})
                resp.raise_for_status()
                print(f"✅ Batch {i//batch_size + 1}", flush=True)
            except Exception as e:
                print(f"⚠️ Failed batch {i//batch_size + 1}: {e}", flush=True)

async def main():
    await seed_orders(n=400, batch_size=25)
    print("🏁 DONE")

if __name__ == "__main__":
    asyncio.run(main())