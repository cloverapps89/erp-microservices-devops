from fastapi import FastAPI, Request          # 1) Bring in FastAPI framework
import os                            # 2) We'll read an env var for the inventory URL (handy for Docker/Compose)
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
import httpx                         # 3) HTTP client we'll use to call the inventory service

app = FastAPI(title="Orders Service")  # 4) Create the app instance (Uvicorn will run this)

templates = Jinja2Templates(directory="templates")

# 5) Where is the inventory service?  
#    - During local dev (two terminals): it’s on http://127.0.0.1:8000
#    - In Docker Compose: it will be http://inventory-service:8000
INVENTORY_URL = os.getenv("INVENTORY_URL", "http://inventory-service:8000")

@app.get("/orders")                   # 6) Simple endpoint: pretend these came from a DB
def get_orders():

    #orders = ["Order1", "Order2", "Order3"]
    orders = []
    return {"orders": orders}

@app.get("/orders-with-inventory", response_class=HTMLResponse)
def get_orders_with_inventory(request: Request):
    try:
        resp = httpx.get(f"{INVENTORY_URL}/api/inventory", timeout=5.0)
        resp.raise_for_status()
        inventory_data = resp.json()
        inventory = inventory_data.get("inventory", [])
    except httpx.HTTPStatusError as e:
        return templates.TemplateResponse(request,"index.html", {
            "error": f"Inventory responded with {e.response.status_code}",
            "orders": [],
            "inventory": []
        })
    except httpx.RequestError as e:
        return templates.TemplateResponse(request,"index.html", {
            "error": f"Could not reach inventory: {str(e)}",
            "orders": [],
            "inventory": []
        })

    orders = ["Order1", "Order2", "Order3"]
    #orders = []

    return templates.TemplateResponse(request,"index.html", {
        "orders": orders,
        "inventory": inventory
    })

@app.get("/api/orders-with-inventory", response_class=HTMLResponse)
def get_orders_with_inventory(request: Request):
    try:
        resp = httpx.get(f"{INVENTORY_URL}/api/inventory", timeout=5.0)
        resp.raise_for_status()
        inventory = resp.json()
    except httpx.HTTPStatusError as e:
        return JSONResponse(content= {
            "error": f"Inventory responded with {e.response.status_code}",
            "orders": [],
            "inventory": []
        })
    except httpx.RequestError as e:
        return JSONResponse(content= {
            "error": f"Could not reach inventory: {str(e)}",
            "orders": [],
            "inventory": []
        })

    orders = ["Order1", "Order2", "Order3"]
    #orders = []
    print(inventory)
    return JSONResponse(content={"orders": orders, "inventory": inventory})