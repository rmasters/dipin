from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from .routers.public import router as public_router
from .routers.admin import router as admin_router


app = FastAPI()

app.mount(
    "/static", StaticFiles(directory=Path(__file__).parent / "static"), name="static"
)
app.include_router(public_router)
app.include_router(admin_router, prefix="/admin")
