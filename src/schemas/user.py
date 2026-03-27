from datetime import date, datetime
from typing import Self
import re
from typing import Optional
from pydantic import BaseModel, EmailStr, Field, field_validator, ConfigDict
from src.models.user import GenderEnum


class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class TokenPayload(BaseModel):
    sub: str
    exp: int


class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(
        min_length=8, description="Password must be at least 8 characters long"
    )

    @field_validator("password")
    @classmethod
    def validate_password_complexity(cls, value: str) -> Self:
        if not re.search(r"A-Z]", value):
            raise ValueError("Password must contain at least one uppercase letter")
        if not re.search(r"a-z]", value):
            raise ValueError("Password must contain at least one lowercase letter")
        if not re.search(r"[0-9]", value):
            raise ValueError("Password must contain at least one number")
        if not re.search(r"[`~/.,!@#*<>_&=+]", value):
            raise ValueError(
                "Password must contain at least one special character (e.g., !, @, #, *)"
            )
        return value


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserProfileBase(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    avatar: Optional[str] = None
    gender: Optional[GenderEnum] = None
    date_of_birth: Optional[date] = None
    info: Optional[str] = None


class UserProfileUpdate(UserProfileBase):
    pass


class UserProfileRead(UserProfileBase):
    id: int
    user_id: int

    model_config = ConfigDict(from_attributes=True)


class UserRead(BaseModel):
    id: int
    email: EmailStr
    is_active: bool
    group_id: int
    created_at: datetime
    updated_at: datetime
    profile: Optional[UserProfileRead] = None

    model_config = ConfigDict(from_attributes=True)
