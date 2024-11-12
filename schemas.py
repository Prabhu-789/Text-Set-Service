# schemas.py
from pydantic import BaseModel
from uuid import UUID

class CreateTextSet(BaseModel):
    title: str
    description: str

    class Config:
        from_attributes = True

class TextSetResponse(CreateTextSet):
    id: UUID

    class Config:
        from_attributes = True

class GetResponse(CreateTextSet):
    textsetId: UUID
    registered_user_id: UUID  # Include user ID in response

    class Config:
        from_attributes = True
# schemas.py


class User(BaseModel):
    id: int
    name: str
    city: str
    isMale: bool

    class Config:
        from_attributes = True

class RegisteredUserCreate(BaseModel):
    user_name: str
    email: str
    password: str  # Plain password input

    class Config:
        from_attributes = True

class RegisteredUserResponse(BaseModel):
    id: UUID
    user_name: str

    class Config:
        from_attributes = True
