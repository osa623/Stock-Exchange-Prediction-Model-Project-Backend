from fastapi import FastAPI

from contextlib import asynccontextmanager
from db.session import engine, Base
# import models to register them with Base
from db import models

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create tables
    Base.metadata.create_all(bind=engine)
    yield

app = FastAPI(title="Stock Exchange Prediction API", lifespan=lifespan)

@app.get("/home")
def welcome_message():
    return {"message": "Welcome to the Stock Exchange Prediction API"}
