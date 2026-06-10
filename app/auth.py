import os
from datetime import datetime, timedelta, timezone
from typing import Annotated
from dotenv import load_dotenv
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from app.settings import ENV_PATH
from pwdlib import PasswordHash
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.db import get_db
from app.models import User
import jwt
from jwt.exceptions import InvalidTokenError
from app.schemas import Token, TokenData

load_dotenv(ENV_PATH)

SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM")
ACCESS_TOKEN_EXPIRE_MINUTES = 30

password_hash = PasswordHash.recommended()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


def verify_password(plain_password, hashed_password):
    return password_hash.verify(plain_password, hashed_password)


def get_password_hash(password):
    return password_hash.hash(password)


def get_user(session: Annotated[Session, Depends(get_db)], email: str):
    stmt = select(User).where(User.email == email)
    user = session.scalars(stmt).one_or_none()
    if not user:
        return None
    return user


def authenticate_user(email: str, password: str, session: Annotated[Session, Depends(get_db)]):
    user = get_user(session, email)
    if user is None:
        return {'data': "User does not exist"}
    if not verify_password(password, user.hashed_password):
        return {'data': "Wrong password"}
    return user


def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


async def get_current_user(token: Annotated[str, Depends(oauth2_scheme)], session: Annotated[Session, Depends(get_db)],):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email = payload.get("sub")
        if email is None:
            raise credentials_exception
        token_data = TokenData(email=email)
    except InvalidTokenError:
        raise credentials_exception
    user = get_user(email=token_data.email, session=session)
    if user is None:
        raise credentials_exception
    return user


async def get_current_active_user(
        current_user: Annotated[User, Depends(get_current_user)],
):
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    elif not current_user.session.active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user

# sessio = Session(engine)
# # with Session(engine) as session:
# #     new_user = User(fullname='Andrey', email='test@asd.com', hashed_password=get_password_hash('123'), is_active=True)
# #     session.add(new_user)
# #     session.commit()
# user = authenticate_user('test@asd.com', '123', sessio)
#
# access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
#
# access_token = create_access_token(
#     data={"sub": user.email}, expires_delta=access_token_expires
# )
#
# toke = Token(access_token=access_token, token_type="bearer")
# get_current_user(toke.access_token, sessio)
# use = get_current_user(toke.access_token, sessio)
# print(use)


