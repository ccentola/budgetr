import json
from fastapi import Depends, APIRouter
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
from plaid.exceptions import ApiException
from plaid.model.transactions_sync_request import TransactionsSyncRequest
from sqlalchemy.orm import Session
from .. import crud, plaid_config
from ..database import get_db

router = APIRouter()


@router.post("/api/transactions")
def get_transactions(access_token: str, item_id: str, db: Session = Depends(get_db)):
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
            response = plaid_config.client.transactions_sync(request).to_dict()
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
