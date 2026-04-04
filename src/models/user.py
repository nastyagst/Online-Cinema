import enum
from datetime import datetime, timezone

from sqlalchemy import (
    Column,
    Integer,
    String,
    DateTime,
    ForeignKey,
    Date,
    Text,
    Enum,
    Boolean,
)
from sqlalchemy.orm import relationship

from src.db.database import Base


class UserGroupEnum(str, enum.Enum):
    USER = "USER"
    MODERATOR = "MODERATOR"
    ADMIN = "ADMIN"


class GenderEnum(str, enum.Enum):
    MAN = "MAN"
    WOMAN = "WOMAN"


class UserGroup(Base):
    __tablename__ = "user_groups"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(
        Enum(UserGroupEnum, name="user_group_enum"), unique=True, nullable=False
    )

    users = relationship("User", back_populates="group")


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=True)
    hashed_password = Column(String, nullable=False)
    is_active = Column(Boolean, default=False)
    created_at = Column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    updated_at = Column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    group_id = Column(Integer, ForeignKey("user_groups.id"), nullable=False)

    group = relationship("UserGroup", back_populates="users")
    profile = relationship("UserProfile", back_populates="user", uselist=False)
    activation_token = relationship(
        "ActivationToken", back_populates="user", uselist=False
    )
    password_reset_token = relationship(
        "PasswordResetToken", back_populates="user", uselist=False
    )
    refresh_tokens = relationship("RefreshToken", back_populates="user")
    cart = relationship("Cart", back_populates="user", uselist=False, lazy="joined")
    orders = relationship("Order", back_populates="user")


class UserProfile(Base):
    __tablename__ = "user_profiles"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    first_name = Column(String, nullable=True)
    last_name = Column(String, nullable=True)
    avatar = Column(String, unique=True)
    gender = Column(Enum(GenderEnum, name="gender_enum"), nullable=True)
    date_of_birth = Column(Date, nullable=True)
    info = Column(Text, nullable=True)

    user = relationship("User", back_populates="profile")


class ActivationToken(Base):
    __tablename__ = "activation_tokens"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    token = Column(String, unique=True, index=True, nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=False)

    user = relationship("User", back_populates="activation_token")


class PasswordResetToken(Base):
    __tablename__ = "password_reset_tokens"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    token = Column(String, unique=True, index=True, nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=False)

    user = relationship("User", back_populates="password_reset_token")


class RefreshToken(Base):
    __tablename__ = "refresh_tokens"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    token = Column(String, unique=True, index=True, nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=False)

    user = relationship("User", back_populates="refresh_tokens")
