from fastapi import Depends, APIRouter
from sqlalchemy.orm import Session
from .. import crud
from ..database import get_db

router = APIRouter()


@router.get("/api/items")
async def get_items(db: Session = Depends(get_db)):
    user_id = 1
    items = crud.get_all_items_for_user(db, user_id)
    return items
