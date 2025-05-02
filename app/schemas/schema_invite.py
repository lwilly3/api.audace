from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime

class InviteRequest(BaseModel):
    email: EmailStr

class InviteResponse(BaseModel):
    token: str
    expires_at: datetime

class ValidateInviteResponse(BaseModel):
    valid: bool
    email: EmailStr

class SignupWithInviteRequest(BaseModel):
    token: str
    username: str
    email: EmailStr
    password: str
    name: str
    family_name: str
    phone_number: Optional[str] = None
    profilePicture: Optional[str] = None

    model_config = {"from_attributes": True}