from fastapi import FastAPI          # 1) Bring in FastAPI framework
import os                            # 2) We'll read an env var for the inventory URL (handy for Docker/Compose)
import httpx                         # 3) HTTP client we'll use to call the inventory service

app = FastAPI(title="Orders Service")  # 4) Create the app instance (Uvicorn will run this)

# 5) Where is the inventory service?  
#    - During local dev (two terminals): it’s on http://127.0.0.1:8000
#    - In Docker Compose: it will be http://inventory-service:8000
INVENTORY_URL = os.getenv("INVENTORY_URL", "http://inventory-service:8000")

@app.get("/orders")                   # 6) Simple endpoint: pretend these came from a DB
def get_orders():
    return {"orders": ["Order1", "Order2", "Order3"]}

@app.get("/orders-with-inventory")    # 7) Composite endpoint: fetch inventory from the other service
def get_orders_with_inventory():
    try:
        # 8) Call the inventory service’s /inventory endpoint
        resp = httpx.get(f"{INVENTORY_URL}/inventory", timeout=5.0)
        resp.raise_for_status()       # 9) Raise on HTTP errors (like 404/500)
        inventory = resp.json()
    except httpx.HTTPStatusError as e:
        return {"error": f"Inventory responded with {e.response.status_code}"}
    except httpx.RequestError as e:
        return {"error": f"Could not reach inventory: {str(e)}"}

    # 10) Merge a tiny orders list with the fetched inventory
    return {"orders": ["Order1", "Order2", "Order3"], "inventory": inventory}
