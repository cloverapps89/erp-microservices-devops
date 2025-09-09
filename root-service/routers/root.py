import os
from pathlib import Path
from fastapi import APIRouter,Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates



PROJECT_ROOT = Path(__file__).resolve().parent.parent
TEMPLATES_DIR = PROJECT_ROOT  / "templates"
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

router = APIRouter()
# ---------------------------
# Service URLs
# ---------------------------
INVENTORY_URL = os.getenv("INVENTORY_URL", "http://inventory-service:8001")
ORDERS_URL = os.getenv("ORDERS_URL", "http://orders-service:8002")
VENDOR_URL = os.getenv("VENDOR_URL", "http://vendor-service:8003")

PUBLIC_INVENTORY_URL = os.getenv("PUBLIC_INVENTORY_URL", "http://127.0.0.1:8001")
PUBLIC_ORDERS_URL = os.getenv("PUBLIC_ORDERS_URL", "http://127.0.0.1:8002")
PUBLIC_VENDOR_URL = os.getenv("PUBLIC_VENDOR_URL","http://127.0.0.1:8003")

# ---------------------------
# Routes
# ---------------------------
@router.get("/", response_class=HTMLResponse)
def index(request: Request):
    """Landing page with links to orders and inventory dashboards."""
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "orders": PUBLIC_ORDERS_URL,
            "inventory": PUBLIC_INVENTORY_URL,
            "vendors": PUBLIC_VENDOR_URL
        }
    )