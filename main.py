import os
import time
import json
from pydantic import BaseModel
from typing import List, Optional
from datetime import date, timedelta
import plaid
from plaid.api import plaid_api
from fastapi import FastAPI, HTTPException, Request
from fastapi.encoders import jsonable_encoder
from dotenv import load_dotenv
from plaid.model.products import Products
from plaid.model.country_code import CountryCode
from plaid.model.link_token_create_request import LinkTokenCreateRequest
from plaid.model.link_token_create_request_user import LinkTokenCreateRequestUser

load_dotenv()

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

app = FastAPI()


@app.get("/")
async def root():
    return {"message": "Hello World"}


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
