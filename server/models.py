from sqlalchemy import Column, Integer, String, ForeignKey, Float
from sqlalchemy.orm import relationship

from .database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    email = Column(String, unique=True, index=True)

    items = relationship("Item", back_populates="owner")
    transactions = relationship("Transaction", back_populates="owner")


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
    transactions = relationship("Transaction", back_populates="account")


class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    account_id = Column(String, ForeignKey("accounts.id"))
    category = Column(String)
    date = Column(String)
    authorized_date = Column(String)
    name = Column(String)
    amount = Column(Float)
    currency_code = Column(String)
    is_removed = Column(Integer, default=0)

    owner = relationship("User", back_populates="transactions")
    account = relationship("Account", back_populates="transactions")
