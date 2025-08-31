import os
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles


    
#Initialize the app
app = FastAPI()

#Setup templating
templates = Jinja2Templates(directory="templates")

# Inside services (backend API calls)
ORDERS_URL = os.getenv("ORDERS_URL", "http://orders-service:8001")
INVENTORY_URL = os.getenv("INVENTORY_URL", "http://inventory-service:8000")

# For browser-facing links
PUBLIC_ORDERS_URL = os.getenv("PUBLIC_ORDERS_URL", "http://127.0.0.1:8001")
PUBLIC_INVENTORY_URL = os.getenv("PUBLIC_INVENTORY_URL", "http://127.0.0.1:8000")


@app.get("/", response_class=HTMLResponse)
def index(request: Request):
    return templates.TemplateResponse(request, "index.html", {"request": request, "orders": PUBLIC_ORDERS_URL, "inventory": PUBLIC_INVENTORY_URL})

@app.get("/inventory", response_class=HTMLResponse)
def getInventory(request: Request):
    items = [
    {"name": "Apples", "sku": "APL123", "quantity": 42},
    {"name": "Bananas", "sku": "BAN456", "quantity": 30},
    {"name": "Oranges", "sku": "ORG789", "quantity": 5}
    ]

    # Define your emoji map
    emoji_map = {
    "apples": "🍎",
    "bananas": "🍌",
    "oranges": "🍊",
    "grapes": "🍇"
    }

    # Normalize and enrich each item
    for item in items:
        normalized_name = item["name"].strip().lower()
        item["normalized_name"] = normalized_name
        item["symbol"] = emoji_map.get(normalized_name, "🏷️")  # fallback symbol

    return templates.TemplateResponse(request,"inventory.html", {"request": request, "items": items})

@app.get("/api/inventory")
def get_inventory_json():
    items = [
        {"name": "Apples", "sku": "APL123", "quantity": 42},
        {"name": "Bananas", "sku": "BAN456", "quantity": 30},
        {"name": "Oranges", "sku": "ORG789", "quantity": 5}
    ]

    emoji_map = {
        "apples": "🍎",
        "bananas": "🍌",
        "oranges": "🍊",
        "grapes": "🍇"
    }

    for item in items:
        normalized_name = item["name"].strip().lower()
        item["normalized_name"] = normalized_name
        item["symbol"] = emoji_map.get(normalized_name, "🏷️")

    return JSONResponse(content={"inventory": items})