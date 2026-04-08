from contextlib import asynccontextmanager
import asyncio

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app import models  # noqa: F401
from app.core.config import settings
from app.core.database import Base, engine, session_scope
from app.routers.api_records import router as api_records_router
from app.routers.health import router as health_router
from app.routers.web_records import router as web_records_router
from app.routers.web_settings import router as web_settings_router
from app.services.mapping_service import ensure_default_template
from app.services.sftp_transfer_service import sftp_transfer_loop


@asynccontextmanager
async def lifespan(app: FastAPI):
    stop_event = asyncio.Event()
    Base.metadata.create_all(bind=engine)
    with session_scope() as session:
        ensure_default_template(session)
    transfer_task = asyncio.create_task(sftp_transfer_loop(stop_event))
    try:
        yield
    finally:
        stop_event.set()
        await transfer_task


app = FastAPI(title=settings.app_name, lifespan=lifespan)
app.mount("/static", StaticFiles(directory="app/static"), name="static")

app.include_router(health_router)
app.include_router(api_records_router)
app.include_router(web_records_router)
app.include_router(web_settings_router)
