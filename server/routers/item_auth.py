from fastapi import Depends, APIRouter
from fastapi.responses import JSONResponse

from fastapi.encoders import jsonable_encoder
from plaid.model.auth_get_request import AuthGetRequest

from plaid.exceptions import ApiException
from sqlalchemy.orm import Session

from .. import crud, plaid_config
from ..database import get_db

router = APIRouter()


@router.post("/api/auth")
def get_auth(db: Session = Depends(get_db)):
    try:
        access_token = crud.get_latest_access_token(db, 1)
        request = AuthGetRequest(access_token=access_token)
        response = plaid_config.client.auth_get(request)
        return jsonable_encoder(response.to_dict())
    except ApiException as e:
        return JSONResponse(status_code=e.status, content=e.body)
