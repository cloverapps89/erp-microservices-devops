from fastapi import FastAPI
from health import router as health_router
from routers import root

# ---------------------------
# App setup
# ---------------------------
app = FastAPI()

# Routers
app.include_router(health_router)
app.include_router(root.router, prefix="", tags=["root"])