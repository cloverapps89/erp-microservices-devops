import os
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
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

@app.get("/inventory")
def getInventory():
    return {"items": ["Apples","Bananas", "Oranges"]}