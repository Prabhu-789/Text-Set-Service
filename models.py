from sqlalchemy import Column, String, DateTime, ForeignKey, TIMESTAMP
from sqlalchemy.dialects.postgresql import UUID
from uuid import uuid4
from database import Base
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

class RegisteredUser(Base):
    __tablename__ = 'RegisteredUser'
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_name = Column(String, nullable=False, unique=True)
    email = Column(String, nullable=False, unique=True)
    hashed_password = Column(String, nullable=False)
    created_at = Column(TIMESTAMP, server_default=func.now())

    # Updated relationship
    textsets = relationship("TextSet", back_populates="registered_user")

class TextSet(Base):
    __tablename__ = "TextSet"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)  # Rename from textsetId to id
    title = Column(String, nullable=False, unique=True)
    description = Column(String, nullable=False)
    created_at = Column(TIMESTAMP, server_default=func.now())
    owner_id = Column(UUID(as_uuid=True), ForeignKey('RegisteredUser.id'))  # Rename from registered_user_id to owner_id

    registered_user = relationship("RegisteredUser", back_populates="textsets")
    
