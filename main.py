# main.py
from fastapi import FastAPI
from controller import router
from uploadfile import route
import models
from database import engine

app = FastAPI()

# Create database tables on startup
models.Base.metadata.create_all(bind=engine)

# Include the router for authentication and TextSet-related endpoints
app.include_router(router)
app.include_router(route)

