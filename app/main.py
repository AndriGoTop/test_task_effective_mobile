from datetime import timedelta
from typing import Annotated
from fastapi import FastAPI, Depends, status, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from sqlalchemy import select
from app.auth import get_password_hash, authenticate_user, ACCESS_TOKEN_EXPIRE_MINUTES, create_access_token, \
    get_current_active_user, verify_password
from app.db import get_db
from app.schemas import SignUp, Token, ResponseUser, UserUpdate
from app.models import User, UserSession

app = FastAPI()
SessionDep = Annotated[Session, Depends(get_db)]


@app.post('/sign_up')
def sign_up(data: SignUp, session: SessionDep):
    password = data.password.get_secret_value()
    repeat_password = data.repeat_password.get_secret_value()
    if password != repeat_password:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="Пароли не совпадают")
    check_user = session.scalars(select(User).where(User.email == data.email)).one_or_none()
    if check_user is not None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="Пользователь с такой почтой уже зарегистрирован")
    new_user = User(fullname=data.fullname, email=data.email,
                    hashed_password=get_password_hash(password=password),
                    is_active=True)
    session.add(new_user)
    session.commit()
    return {"data": data}


@app.post("/token")
async def login_for_access_token(form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
                                 session: SessionDep) -> Token:
    user = authenticate_user(form_data.username, form_data.password, session)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )

    stmt = select(UserSession).where(UserSession.user_id == user.id)
    res_stmt = session.scalars(stmt).one_or_none()
    if res_stmt is None:
        new_session = UserSession(
            token_hash='access_token',
            user=user,
            active=True
        )
        session.add(new_session)
    else:
        res_stmt.token_hash = access_token
        res_stmt.active = True

    session.commit()

    return Token(access_token=access_token, token_type="bearer")


@app.post("/logout")
async def logout(current_user: Annotated[ResponseUser, Depends(get_current_active_user)], session: SessionDep):
    user = current_user.session
    user.active = False
    session.commit()

    return status.HTTP_200_OK


@app.patch("/users")
async def update_data_user(data: UserUpdate, current_user: Annotated[ResponseUser, Depends(get_current_active_user)],
                           session: SessionDep):
    user = current_user
    if data.email is not None:
        if verify_password(data.password.get_secret_value(), user.hashed_password):
            user.email = data.email
        else:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Введён неверный пароль")

    if data.fullname is not None:
        user.fullname = data.fullname

    if data.new_password is not None:
        if data.new_password.get_secret_value() == data.repeat_password.get_secret_value():
            if verify_password(data.password.get_secret_value(), user.hashed_password):
                user.hashed_password = data.new_password.get_secret_value()
            else:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Введён неверный пароль")
        else:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                                detail="Пароль не совпадает с его повторным вводом")

    session.commit()
    return data


@app.get("/users/me/")
async def read_users_me(
        current_user: Annotated[ResponseUser, Depends(get_current_active_user)],
) -> ResponseUser:
    return current_user
