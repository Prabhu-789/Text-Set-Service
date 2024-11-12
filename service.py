# # service.py
# from sqlalchemy.orm import Session
# from fastapi import HTTPException, status
# from schemas import CreateTextSet,TextSetResponse
# import models
# from typing import Set
# from passlib.hash import bcrypt 
# from models import RegisteredUser, TextSet
# from passlib.hash import bcrypt # type: ignore
# from schemas import RegisteredUserCreate, RegisteredUserResponse
# from sqlalchemy.exc import SQLAlchemyError

# from uuid import UUID
# from auth import create_access_token
# import logging
# logger=logging.getLogger(__name__)
# class TextSetService:
#     def __init__(self, db: Session):
#         self.db = db
    
#     def create_text_set(self, text_set: CreateTextSet, username: str) -> TextSetResponse:
#         # Check if a TextSet with the same title already exists (optional)
#         existing_text_set = self.db.query(models.TextSet).filter(models.TextSet.title == text_set.title).first()
#         if existing_text_set:
#             raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="TextSet with this title already exists")
        
#         # Get the user ID from the username (you can also use the username directly if necessary)
#         user = self.db.query(models.RegisteredUser).filter(models.RegisteredUser.user_name == username).first()
#         if not user:
#             raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
        
#         # Create the TextSet entry
#         new_text_set = models.TextSet(
#             title=text_set.title,
#             description=text_set.description,
#             registered_user_id=user.id  # Link to the user who is creating the text set
#         )
        
#         try:
#             self.db.add(new_text_set)
#             self.db.commit()
#             self.db.refresh(new_text_set)
#         except SQLAlchemyError as e:
#             self.db.rollback()
#             raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error saving TextSet")
        
#         return TextSetResponse(textsetId=new_text_set.textsetId,title=new_text_set.title,description=new_text_set.description)
    
#     def get_text_set(self) -> list[TextSetResponse]:
#         try:
#             # Retrieve all TextSet objects from the database
#             return self.db.query(models.TextSet).all()
#         except SQLAlchemyError as e:
#             logger.error(f"Error fetching TextSets: {str(e)}")
#             raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error fetching TextSets")

# class UserService:
#     def __init__(self, db: Session):
#         self.db = db

#     # In-memory set to store blacklisted tokens
#     blacklisted_tokens: Set[str] = set()

    

#     def register_user(self, Ruser: RegisteredUserCreate) -> RegisteredUserResponse:
#         hashed_password = bcrypt.hash(Ruser.password)  # Correctly hash the password
#         new_user = models.RegisteredUser(
#         user_name=Ruser.user_name,  # Ensure the field is user_name in your model
#         email = Ruser.email,
#         hashed_password=hashed_password
#          )
#         try:
#             self.db.add(new_user)
#             self.db.commit()
#             self.db.refresh(new_user)
#         except SQLAlchemyError as e:
#             self.db.rollback()  # Rollback in case of failure
#             print(f"Error registering user: {str(e)}")
#             raise

#         return RegisteredUserResponse(id=new_user.id, user_name=new_user.user_name)
    
#     def login(self, username: str, password: str) -> str:
#         try:
#             user = self.db.query(models.RegisteredUser).filter(models.RegisteredUser.user_name == username).first()
#         except SQLAlchemyError as e:
#             print(f"Error during login: {str(e)}")
#             raise

#         if not user or not bcrypt.verify(password, user.hashed_password):
#             return None
#         return create_access_token(data={"sub": user.user_name})
    
#     def is_token_blacklisted(self, token: str) -> bool:
#         return token in self.blacklisted_tokens
    
    
# service.py
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from fastapi import HTTPException, status
from passlib.hash import bcrypt
from uuid import UUID
from models import RegisteredUser, TextSet
from schemas import RegisteredUserCreate, RegisteredUserResponse, CreateTextSet, TextSetResponse
from auth import create_access_token
import logging

logger = logging.getLogger(__name__)

class TextSetService:
    def __init__(self, db: Session):
        self.db = db

    def create_text_set(self, text_set: CreateTextSet, user_id: UUID) -> TextSetResponse:
        existing_text_set = self.db.query(TextSet).filter(TextSet.title == text_set.title).first()
        if existing_text_set:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="TextSet with this title already exists")
        
        new_text_set = TextSet(
        title=text_set.title,
        description=text_set.description,
        owner_id=user_id  # Ensure this is a UUID
    )
        
        try:
            self.db.add(new_text_set)
            self.db.commit()
            self.db.refresh(new_text_set)
        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(f"Error saving TextSet: {str(e)}")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error saving TextSet")
        
        return TextSetResponse(id=new_text_set.id, title=new_text_set.title, description=new_text_set.description)

    def get_text_set(self) -> list[TextSetResponse]:
        try:
            return self.db.query(TextSet).all()
        except SQLAlchemyError as e:
            logger.error(f"Error fetching TextSets: {str(e)}")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error fetching TextSets")


class UserService:
    blacklisted_tokens = set()

    def __init__(self, db: Session):
        self.db = db

    def register_user(self, Ruser: RegisteredUserCreate) -> RegisteredUserResponse:
        hashed_password = bcrypt.hash(Ruser.password)
        new_user = RegisteredUser(
            user_name=Ruser.user_name,
            email=Ruser.email,
            hashed_password=hashed_password
        )
        
        try:
            self.db.add(new_user)
            self.db.commit()
            self.db.refresh(new_user)
        except IntegrityError:
            self.db.rollback()
            logger.error("Username or email already exists.")
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Username or email already exists.")
        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(f"Database error during user registration: {str(e)}")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to register user")
        
        return RegisteredUserResponse(id=new_user.id, user_name=new_user.user_name)

    def login(self, username: str, password: str) -> str:
        user = self.db.query(RegisteredUser).filter(RegisteredUser.user_name == username).first()
        if not user or not bcrypt.verify(password, user.hashed_password):
            logger.warning("Invalid login credentials.")
            return None
    # Pass user ID instead of username to create_access_token
        return create_access_token(data={"sub": str(user.id)})

    def is_token_blacklisted(self, token: str) -> bool:
        return token in self.blacklisted_tokens
