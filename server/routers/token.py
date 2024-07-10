import time
import json
from fastapi import Depends, HTTPException, APIRouter, Request, Body
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from plaid.model.country_code import CountryCode
from plaid.model.link_token_create_request import LinkTokenCreateRequest
from plaid.model.link_token_create_request_user import LinkTokenCreateRequestUser
from plaid.model.item_public_token_exchange_request import (
    ItemPublicTokenExchangeRequest,
)
from plaid.model.item_public_token_exchange_response import (
    ItemPublicTokenExchangeResponse,
)
from plaid.exceptions import ApiException
from .. import crud, plaid_config
from ..database import get_db

router = APIRouter()


@router.post("/api/create_link_token")
async def create_link_token(request: Request):
    try:
        request = LinkTokenCreateRequest(
            products=plaid_config.products,
            client_name="budgetr",
            country_codes=list(
                map(lambda x: CountryCode(x), plaid_config.PLAID_COUNTRY_CODES)
            ),
            language="en",
            user=LinkTokenCreateRequestUser(client_user_id=str(time.time())),
        )

        response = plaid_config.client.link_token_create(request)
        return response.to_dict()
    except plaid_config.ApiException as e:
        print(e)
        raise HTTPException(status_code=e.status, detail=json.loads(e.body))


@router.post("/api/set_access_token")
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
            plaid_config.client.item_public_token_exchange(exchange_request)
        )
        access_token = exchange_response.access_token
        item_id = exchange_response.item_id
        # add item to db
        crud.add_item(db, user_id=user_id, access_token=access_token, item_id=item_id)
        # crud.add_item(db, item=item)
        return JSONResponse(content=exchange_response.to_dict())
    except ApiException as e:
        return JSONResponse(status_code=e.status, content=e.body)
