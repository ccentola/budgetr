import json
from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
from plaid.model.accounts_balance_get_request import AccountsBalanceGetRequest
from plaid.exceptions import ApiException
from sqlalchemy.orm import Session
from .. import crud, plaid_config
from ..database import get_db

router = APIRouter()


@router.post("/api/balance")
def get_balance(db: Session = Depends(get_db)):
    try:
        # get most recent access token for testing
        access_token = crud.get_latest_access_token(db, 1)
        request = AccountsBalanceGetRequest(access_token=access_token)
        response = plaid_config.client.accounts_balance_get(request)
        data = jsonable_encoder(response.to_dict())
        with open("data/balances.json", "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        return data
    except ApiException as e:
        return JSONResponse(status_code=e.status, content=e.body)
