from fastapi import FastAPI
from .db import Base, engine
from . import models
from .api import router

Base.metadata.create_all(engine)
app = FastAPI(title="Analysis Server")
app.include_router(router)