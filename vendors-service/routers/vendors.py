import os
from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
TEMPLATES_DIR = PROJECT_ROOT  / "templates"
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

router = APIRouter()

# Check root
VENDORS_URL = os.getenv("VENDORS_URL", "http://vendors-service:8003")

@router.get("", response_class=HTMLResponse)
def index(request: Request):
    """Landing page for vendors."""
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request
        }
    )