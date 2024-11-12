
# # controllers.py
# from fastapi import APIRouter, HTTPException, Depends, status
# from sqlalchemy.orm import Session
# from database import SessionLocal
# from service import UserService, TextSetService
# from sqlalchemy.exc import SQLAlchemyError
# from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
# from schemas import RegisteredUserCreate, RegisteredUserResponse, TextSetResponse,CreateTextSet
# from auth import verify_access_token
# import logging

# router = APIRouter()

# logger=logging.getLogger(__name__)


# oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

# def get_db():
#     db = SessionLocal()
#     try:
#         yield db
#     finally:
#         db.close()

# # controller.py

# def authenticate_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
#     service = UserService(db)
#     if service.is_token_blacklisted(token):
#         raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token has been logged out")
    
#     try:
#         user_id = verify_access_token(token)  # This will give us the user_id (UUID)
#         if not user_id:
#             raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
#     except Exception as e:
#         logger.error(f"Token verification failed: {str(e)}")
#         raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token verification failed")
    
#     return user_id


# @router.post('/signup', response_model=RegisteredUserResponse, status_code=status.HTTP_201_CREATED)
# def register_user(Ruser: RegisteredUserCreate, db: Session = Depends(get_db)):
#     logger.info(f"Registering new user: {Ruser.user_name}")
#     service = UserService(db)
#     try:
#         new_user = service.register_user(Ruser)
#     except SQLAlchemyError as e:
#         logger.error(f"Failed to register user: {str(e)}")
#         raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to register user")
    
#     logger.info(f"User {new_user.user_name} registered successfully")
#     return new_user

# @router.post('/login', response_model=dict)
# def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
#     service = UserService(db)
#     try:
#         token = service.login(form_data.username, form_data.password)
#     except SQLAlchemyError as e:
#         logger.error(f"Login error: {str(e)}")
#         raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Login error")
    
#     if not token:
#         raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
#     return {"access_token": token, "token_type": "bearer"}

# @router.post('/TextSet', response_model=TextSetResponse, status_code=status.HTTP_201_CREATED)
# def create_text_set(
#     text_set: CreateTextSet,  # Receive the title and description as input
#     db: Session = Depends(get_db),  # Dependency to get the database session
#     token: str = Depends(oauth2_scheme)  # Depend on oauth2_scheme to get the JWT token
# ):
#     # Verify and decode the token to get the user's information
#     try:
#         username = verify_access_token(token)  # Verify the token and get the user
#     except Exception as e:
#         logger.error(f"Token verification failed: {str(e)}")
#         raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    
#     # Now we have the user and can proceed with creating the TextSet
#     textset_service = TextSetService(db)
    
#     # Assuming the TextSetService has a method to create a new TextSet
#     try:
#         created_text_set = textset_service.create_text_set(text_set, username=username)  # Pass username or user id
#         return created_text_set
#     except Exception as e:
#         logger.error(f"Failed to create TextSet: {str(e)}")
#         raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to create TextSet")

# @router.get('/TextSet', response_model=list[TextSetResponse], status_code=status.HTTP_200_OK)
# def get_text_set(db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)):
#     try:
#         username = verify_access_token(token)
#     except Exception as e:
#         logger.error(f"Token verification failed: {str(e)}")
#         raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

#     textset_service = TextSetService(db)
#     return textset_service.get_text_set()
# controller.py
from fastapi import APIRouter, HTTPException, Depends, status
from sqlalchemy.orm import Session
from database import SessionLocal
from service import UserService, TextSetService
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from schemas import RegisteredUserCreate, RegisteredUserResponse, TextSetResponse, CreateTextSet
from auth import verify_access_token
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Dependency to authenticate user by token
def authenticate_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    service = UserService(db)
    if service.is_token_blacklisted(token):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token has been logged out")
    
    try:
        user_id = verify_access_token(token)
        if not user_id:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    except Exception as e:
        logger.error(f"Token verification failed: {str(e)}")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token verification failed")
    
    return user_id

@router.post('/signup', response_model=RegisteredUserResponse, status_code=status.HTTP_201_CREATED)
def register_user(Ruser: RegisteredUserCreate, db: Session = Depends(get_db)):
    logger.info(f"Attempting to register new user: {Ruser.user_name}")
    service = UserService(db)
    try:
        new_user = service.register_user(Ruser)
        logger.info(f"User {new_user.user_name} registered successfully")
        return new_user
    except IntegrityError:
        logger.error("Username or email already exists.")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Username or email already exists.")
    except SQLAlchemyError as e:
        logger.error(f"Database error during registration: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to register user")

@router.post('/login', response_model=dict)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    service = UserService(db)
    try:
        token = service.login(form_data.username, form_data.password)
        if not token:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
        return {"access_token": token, "token_type": "bearer"}
    except SQLAlchemyError as e:
        logger.error(f"Database error during login: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Login error")

@router.post('/TextSet', response_model=TextSetResponse, status_code=status.HTTP_201_CREATED)
def create_text_set(text_set: CreateTextSet, db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)):
    user_id = authenticate_user(token, db)
    textset_service = TextSetService(db)
    try:
        created_text_set = textset_service.create_text_set(text_set, user_id=user_id)
        return created_text_set
    except IntegrityError:
        logger.error("TextSet with this title already exists.")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="TextSet with this title already exists.")
    except SQLAlchemyError as e:
        logger.error(f"Database error during TextSet creation: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to create TextSet")

@router.get('/TextSet', response_model=list[TextSetResponse], status_code=status.HTTP_200_OK)
def get_text_set(db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)):
    user_id = authenticate_user(token, db)
    textset_service = TextSetService(db)
    try:
        return textset_service.get_text_set()
    except SQLAlchemyError as e:
        logger.error(f"Database error fetching TextSets: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error fetching TextSets")
