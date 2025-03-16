from fastapi import FastAPI

from .common.routes import router as chatbot_router

app = FastAPI()

app.include_router(chatbot_router)
