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
