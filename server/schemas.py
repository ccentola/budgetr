from pydantic import BaseModel


class UserBase(BaseModel):
    email: str


class UserCreate(UserBase):
    pass


class User(UserBase):
    id: int
    email: str

    class Config:
        orm_mode = True


class ItemBase(BaseModel):
    user_id: int
    access_token: str


class ItemCreate(ItemBase):
    pass


class Item(ItemBase):
    id: int
    user_id: int
    access_token: str

    class Config:
        orm_mode = True


class AccountBase(BaseModel):
    item_id: int
    name: str


class AccountCreate(AccountBase):
    pass


class Account(AccountBase):
    id: int
    item_id: int
    name: str

    class Config:
        orm_mode = True
