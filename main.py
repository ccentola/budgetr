import os
import time
import json
from fastapi import FastAPI, HTTPException, Request, Body
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
from plaid.model.item_public_token_exchange_request import (
    ItemPublicTokenExchangeRequest,
)
from plaid.model.item_public_token_exchange_response import (
    ItemPublicTokenExchangeResponse,
)
from plaid.exceptions import ApiException

load_dotenv()

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
async def get_access_token(public_token: str = Body(..., embed=True)):
    print(public_token)
    global access_token, item_id, transfer_id
    try:
        exchange_request = ItemPublicTokenExchangeRequest(public_token=public_token)
        exchange_response: ItemPublicTokenExchangeResponse = (
            client.item_public_token_exchange(exchange_request)
        )
        access_token = exchange_response.access_token
        item_id = exchange_response.item_id
        return JSONResponse(content=exchange_response.to_dict())
    except ApiException as e:
        return JSONResponse(status_code=e.status, content=e.body)


@app.post("/api/transactions")
def get_transactions():
    # Set cursor to empty to receive all historical updates
    cursor = ""

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
            pretty_print_response(response)

        # Return the 8 most recent transactions
        latest_transactions = sorted(added, key=lambda t: t["date"])[-8:]
        data = jsonable_encoder(latest_transactions)
        with open("data/transactions.json", "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        return data
    except ApiException as e:
        return JSONResponse(status_code=e.status, content=e.body)


@app.post("/api/auth")
def get_auth():
    try:
        request = AuthGetRequest(access_token=access_token)
        response = client.auth_get(request)
        pretty_print_response(response.to_dict())
        return jsonable_encoder(response.to_dict())
    except ApiException as e:
        return JSONResponse(status_code=e.status, content=e.body)
