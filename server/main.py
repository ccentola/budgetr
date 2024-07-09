import os
import time
import json
from fastapi import Depends, FastAPI, HTTPException, Request, Body
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel
from dotenv import load_dotenv
import plaid
from plaid.api import plaid_api
from plaid.model.products import Products
from plaid.model.country_code import CountryCode
from plaid.model.link_token_create_request import LinkTokenCreateRequest
from plaid.model.link_token_create_request_user import LinkTokenCreateRequestUser
from plaid.model.transactions_sync_request import TransactionsSyncRequest
from plaid.model.auth_get_request import AuthGetRequest
from plaid.model.accounts_balance_get_request import AccountsBalanceGetRequest
from plaid.model.accounts_get_request import AccountsGetRequest

# from plaid.model.item_get_request import ItemGetRequest
# from plaid.model.institutions_get_by_id_request import InstitutionsGetByIdRequest
from plaid.model.item_public_token_exchange_request import (
    ItemPublicTokenExchangeRequest,
)
from plaid.model.item_public_token_exchange_response import (
    ItemPublicTokenExchangeResponse,
)
from plaid.exceptions import ApiException
from sqlalchemy.orm import Session
from . import crud, models, schemas
from .database import SessionLocal, engine

load_dotenv()

models.Base.metadata.create_all(bind=engine)


# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


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


PLAID_CLIENT_ID = os.getenv("PLAID_CLIENT_ID")
PLAID_SECRET = os.getenv("PLAID_SECRET")
PLAID_ENV = os.getenv("PLAID_ENV", "sandbox")
PLAID_PRODUCTS = os.getenv("PLAID_PRODUCTS", "transactions").split(",")
PLAID_COUNTRY_CODES = os.getenv("PLAID_COUNTRY_CODES", "US").split(",")

configuration = plaid.Configuration(
    host=plaid.Environment.Sandbox,
    api_key={"clientId": PLAID_CLIENT_ID, "secret": PLAID_SECRET},
)

api_client = plaid.ApiClient(configuration)
client = plaid_api.PlaidApi(api_client)

products = []
for product in PLAID_PRODUCTS:
    products.append(Products(product))

# We store the access_token in memory - in production, store it in a secure
# persistent data store.
access_token = None


def pretty_print_response(response):
    print(json.dumps(response, indent=2, sort_keys=True, default=str))


@app.post("/users/", response_model=schemas.User)
def create_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    db_user = crud.get_user_by_email(db, email=user.email)
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    return crud.create_user(db=db, user=user)


@app.get("/users/", response_model=list[schemas.User])
def read_users(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    users = crud.get_users(db, skip=skip, limit=limit)
    return users


@app.get("/users/{user_id}", response_model=schemas.User)
def read_user(user_id: int, db: Session = Depends(get_db)):
    db_user = crud.get_user(db, user_id=user_id)
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return db_user


@app.post("/api/create_link_token")
async def create_link_token(request: Request):
    try:
        request = LinkTokenCreateRequest(
            products=products,
            client_name="budgetr",
            country_codes=list(map(lambda x: CountryCode(x), PLAID_COUNTRY_CODES)),
            language="en",
            user=LinkTokenCreateRequestUser(client_user_id=str(time.time())),
        )

        response = client.link_token_create(request)
        return response.to_dict()
    except plaid.ApiException as e:
        print(e)
        raise HTTPException(status_code=e.status, detail=json.loads(e.body))


class PublicTokenForm(BaseModel):
    public_token: str


@app.post("/api/set_access_token")
async def get_access_token(
    public_token: str = Body(..., embed=True),
    db: Session = Depends(get_db),
):
    print(public_token)
    global access_token, item_id, transfer_id
    user_id = 1
    try:
        exchange_request = ItemPublicTokenExchangeRequest(public_token=public_token)
        exchange_response: ItemPublicTokenExchangeResponse = (
            client.item_public_token_exchange(exchange_request)
        )
        access_token = exchange_response.access_token
        item_id = exchange_response.item_id
        # add item to db
        crud.add_item(db, user_id=user_id, access_token=access_token, item_id=item_id)
        # crud.add_item(db, item=item)
        return JSONResponse(content=exchange_response.to_dict())
    except ApiException as e:
        return JSONResponse(status_code=e.status, content=e.body)


@app.post("/api/transactions")
def get_transactions(db: Session = Depends(get_db)):
    # Set cursor to empty to receive all historical updates
    cursor = ""

    # get user id
    user_id = 1

    # New transaction updates since "cursor"
    added = []
    modified = []
    removed = []  # Removed transaction ids
    has_more = True
    try:
        # Iterate through each page of new transaction updates for item
        while has_more:
            request = TransactionsSyncRequest(
                access_token=access_token,
                cursor=cursor,
            )
            response = client.transactions_sync(request).to_dict()
            # Add this page of results
            added.extend(response["added"])
            modified.extend(response["modified"])
            removed.extend(response["removed"])
            has_more = response["has_more"]
            # Update cursor to the next cursor
            cursor = response["next_cursor"]
            # Update cursor for item
            crud.add_cursor_for_item(db, cursor, item_id)

        data = jsonable_encoder(added)
        with open("data/transactions.json", "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        for transaction in added:
            category = (transaction.get("category") or [None])[0]
            crud.add_transaction(
                db,
                user_id=user_id,
                account_id=transaction["account_id"],
                category=category,
                date=transaction["date"],
                authorized_date=transaction["authorized_date"],
                name=transaction["name"],
                amount=transaction["amount"],
                currency_code=transaction["iso_currency_code"],
            )
        return data
    except ApiException as e:
        return JSONResponse(status_code=e.status, content=e.body)


@app.post("/api/auth")
def get_auth():
    try:
        request = AuthGetRequest(access_token=access_token)
        response = client.auth_get(request)
        return jsonable_encoder(response.to_dict())
    except ApiException as e:
        return JSONResponse(status_code=e.status, content=e.body)


@app.post("/api/balance")
def get_balance():
    try:
        request = AccountsBalanceGetRequest(access_token=access_token)
        response = client.accounts_balance_get(request)
        data = jsonable_encoder(response.to_dict())
        with open("data/balances.json", "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        return data
    except ApiException as e:
        return JSONResponse(status_code=e.status, content=e.body)


@app.post("/api/accounts")
async def get_accounts(db: Session = Depends(get_db)):
    try:
        request = AccountsGetRequest(access_token=access_token)
        response = client.accounts_get(request)
        data = jsonable_encoder(response.to_dict())
        item_id = data["item"]["item_id"]
        for account in data["accounts"]:
            crud.add_account(
                db,
                item_id=item_id,
                name=account["name"],
                account_id=account["account_id"],
            )
        return jsonable_encoder(response.to_dict())
    except ApiException as e:
        return JSONResponse(status_code=e.status, content=e.body)


@app.get("/api/items")
async def get_items(db: Session = Depends(get_db)):
    user_id = 1
    items = crud.get_all_items_for_user(db, user_id)
    return items
