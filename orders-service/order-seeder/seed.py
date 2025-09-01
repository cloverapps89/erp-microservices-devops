import asyncio
import os
import random
import string
from datetime import datetime, timedelta, timezone
import httpx

# Public service URLs (adjust if running in Docker vs local)
ORDERS_API = os.getenv("ORDERS_API", "http://localhost:8001/orders")
INVENTORY_API = os.getenv("INVENTORY_API", "http://localhost:8000/inventory")

# Base customer data to randomize from
customer_data = [
    {"name": "Alice Johnson",     "nickname": "AJ",     "email": "alice.j@example.com"},
    {"name": "Robert Smith",      "nickname": "Bobby",  "email": "robert.smith@example.com"},
    {"name": "Cynthia Lee",       "nickname": "Cyn",    "email": "cynthia.lee@example.com"},
    {"name": "David Martinez",    "nickname": "Dave",   "email": "d.martinez@example.com"},
    {"name": "Emily Chen",        "nickname": "Em",     "email": "emily.chen@example.com"},
    {"name": "Franklin Wright",   "nickname": "Frank",  "email": "frank.w@example.com"},
    {"name": "Grace Thompson",    "nickname": "Gracie", "email": "grace.t@example.com"},
    {"name": "Henry Patel",       "nickname": "Hank",   "email": "henry.patel@example.com"},
    {"name": "Isabella Nguyen",   "nickname": "Izzy",   "email": "isabella.n@example.com"},
    {"name": "Jason Kim",         "nickname": "Jay",    "email": "jason.kim@example.com"},
]

def random_suffix(length=5):
    """Generate a short random suffix for uniqueness."""
    return ''.join(random.choices(string.ascii_lowercase + string.digits, k=length))

def random_customer():
    """Pick a base customer and return randomized nickname/email."""
    base = random.choice(customer_data)
    suffix = random_suffix()
    return {
        "name": base["name"],  # not unique
        "nickname": f"{base['nickname']}_{suffix}",  # unique
        "email": f"{base['email'].split('@')[0]}_{suffix}@{base['email'].split('@')[1]}"  # unique
    }

def random_timestamp():
    now = datetime.now(timezone.utc)
    delta = timedelta(days=random.randint(0, 30), hours=random.randint(0, 23))
    return now - delta

async def fetch_inventory():
    """Fetch live inventory from inventory-service."""
    async with httpx.AsyncClient(timeout=5.0) as client:
        resp = await client.get(INVENTORY_API, headers={"Accept": "application/json"})
        resp.raise_for_status()
        data = resp.json()
        return data.get("inventory", [])

async def create_order_via_api(order_payload):
    """Send order to orders-service API."""
    async with httpx.AsyncClient(timeout=5.0) as client:
        resp = await client.post(
            ORDERS_API,
            json=order_payload,
            headers={"Accept": "application/json"}
        )
        resp.raise_for_status()
        return resp.json()

async def seed_orders(n=10):
    inventory = await fetch_inventory()
    if not inventory:
        print("❌ No inventory available — cannot seed orders.")
        return

    for _ in range(n):
        order_number = 1000 + random.randint(1, 9999)
        cust = random_customer()

        # Pick 1–5 random items from inventory
        selected_items = random.sample(
            inventory,
            k=min(len(inventory), random.randint(1, 20))
        )

        # Build order payload
        items_payload = []
        for item in selected_items:
            qty = random.randint(1, 3)
            # Skip if not enough stock
            if item["quantity"] < qty:
                continue
            items_payload.append({
                "sku": item["sku"],
                "quantity": qty,
                "price": item["price"]
            })

        if not items_payload:
            continue

        payload = {
            "order_number": order_number,
            "customer_name": cust["name"],
            "customer_nickname": cust["nickname"],
            "customer_email": cust["email"],
            "items": items_payload
        }

        try:
            result = await create_order_via_api(payload)
            print(f"✅ Created order {order_number} for {cust['name']} ({cust['nickname']})")
            print(f"   Updated stock: {result.get('updated_stock')}")
            await asyncio.sleep(0.1) 
        except httpx.HTTPStatusError as e:
            print(f"❌ Failed to create order {order_number}: {e.response.text}")

async def main():
    while True:
        await seed_orders(n=5)  # Number of orders to simulate
        print("✅ ORDER SUBMITTED")
        await asyncio.sleep(10)

if __name__ == "__main__":
    asyncio.run(main())
