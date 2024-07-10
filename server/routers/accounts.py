from fastapi import Depends, APIRouter
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from plaid.model.accounts_get_request import AccountsGetRequest
from plaid.exceptions import ApiException
from .. import crud, plaid_config
from ..database import get_db

router = APIRouter()


@router.post("/api/accounts")
async def get_accounts(db: Session = Depends(get_db)):
    try:
        access_token = crud.get_latest_access_token(db, 1)
        request = AccountsGetRequest(access_token=access_token)
        response = plaid_config.client.accounts_get(request)
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
