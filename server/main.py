from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

from . import models
from .database import engine
from .routers import balance, user, token, transaction, item_auth, accounts, items

load_dotenv()

models.Base.metadata.create_all(bind=engine)

app = FastAPI()

origins = [
    "http://localhost",
    "http://localhost:8080",
    "http://localhost:8000",
    "http://localhost:5500",
    "http://localhost:5173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(balance.router)
app.include_router(user.router)
app.include_router(token.router)
app.include_router(item_auth.router)
app.include_router(accounts.router)
app.include_router(items.router)
app.include_router(transaction.router)
