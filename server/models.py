from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship

from .database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    email = Column(String, unique=True, index=True)

    items = relationship("Item", back_populates="owner")


class Item(Base):
    __tablename__ = "items"

    id = Column(Integer, primary_key=True)
    item_id = Column(String)
    user_id = Column(Integer, ForeignKey("users.id"))
    access_token = Column(String)
    transaction_cursor = Column(String)
    bank_name = Column(String)
    is_active = Column(Integer, default=1)

    owner = relationship("User", back_populates="items")
    accounts = relationship("Account", back_populates="owner")


class Account(Base):
    __tablename__ = "accounts"

    id = Column(Integer, primary_key=True)
    account_id = Column(String)
    item_id = Column(Integer, ForeignKey("items.id"))
    name = Column(String)

    owner = relationship("Item", back_populates="accounts")
