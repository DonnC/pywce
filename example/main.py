from contextlib import asynccontextmanager

from fastapi import FastAPI

from .common.app_logger import setup_logger
from .common.routes import router as chatbot_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logger()
    yield


app = FastAPI(lifespan=lifespan)

app.include_router(chatbot_router)
