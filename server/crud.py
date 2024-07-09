from sqlalchemy.orm import Session

from . import models, schemas


def get_user(db: Session, user_id: int):
    return db.query(models.User).filter(models.User.id == user_id).first()


def get_user_by_email(db: Session, email: str):
    return db.query(models.User).filter(models.User.email == email).first()


def get_users(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.User).offset(skip).limit(limit).all()


def create_user(db: Session, user: schemas.UserCreate):
    db_user = models.User(email=user.email)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


def add_item(db: Session, user_id: int, access_token: str, item_id: str):
    db_item = models.Item(user_id=user_id, item_id=item_id, access_token=access_token)
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return db_item


def add_account(db: Session, item_id: int, name: str, account_id: str):
    db_account = models.Account(item_id=item_id, name=name, account_id=account_id)
    db.add(db_account)
    db.commit()
    db.refresh(db_account)
    return db_account


def add_transaction(
    db: Session,
    user_id: int,
    account_id: str,
    category: str,
    date: str,
    authorized_date: str,
    name: str,
    amount: float,
    currency_code: str,
):
    db_transaction = models.Transaction(
        user_id=user_id,
        account_id=account_id,
        category=category,
        date=date,
        authorized_date=authorized_date,
        name=name,
        amount=amount,
        currency_code=currency_code,
    )
    db.add(db_transaction)
    db.commit()
    db.refresh(db_transaction)
    return db_transaction


def add_cursor_for_item(db: Session, transaction_cursor: str, item_id: str):
    db_item = db.query(models.Item).filter(models.Item.item_id == item_id).first()
    db_item.transaction_cursor = transaction_cursor
    db.commit()
    db.refresh(db_item)
    return db_item


def get_all_items_for_user(db: Session, user_id: int):
    return db.query(models.Item).filter(models.Item.user_id == user_id).all()
