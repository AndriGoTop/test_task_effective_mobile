from datetime import timedelta
from http.client import HTTPResponse
from typing import Annotated
from fastapi import FastAPI, Depends, status, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from sqlalchemy import select, desc
from app.auth import get_password_hash, authenticate_user, ACCESS_TOKEN_EXPIRE_MINUTES, create_access_token, \
    get_current_active_user, verify_password
from app.db import get_db
from app.schemas import SignUp, Token, ResponseUser, UserUpdate, RoleCreate, RoleUpdate, RoleBase, CreatePost, \
    UpdatePost
from app.models import User, UserSession, UsersRoles, Posts

app = FastAPI()
SessionDep = Annotated[Session, Depends(get_db)]


# Пользователи
@app.post('/sign_up', tags=['Пользователь'])
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
    get_role = session.scalars(select(UsersRoles).where(UsersRoles.name_role == data.role)).one_or_none()
    new_user = User(fullname=data.fullname, email=data.email,
                    hashed_password=get_password_hash(password=password),
                    is_active=True, role=get_role)
    session.add(new_user)
    session.commit()
    return {"data": data}


@app.post("/token", tags=['Пользователь'])
async def login_for_access_token(form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
                                 session: SessionDep) -> Token:
    user = authenticate_user(form_data.username, form_data.password, session)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    elif not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User if not active",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": str(user.id)}, expires_delta=access_token_expires
    )

    # Запись сессии
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


@app.post("/logout", tags=['Пользователь'])
async def logout(current_user: Annotated[ResponseUser, Depends(get_current_active_user)], session: SessionDep):
    user = current_user.session
    user.active = False
    session.commit()

    return status.HTTP_200_OK


@app.patch("/users", tags=['Пользователь'])
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


@app.delete('/users', tags=['Пользователь'])
def delete_user(current_user: Annotated[ResponseUser, Depends(get_current_active_user)], session: SessionDep):
    user = current_user
    user.is_active = False
    session.commit()
    return HTTPException(status_code=status.HTTP_204_NO_CONTENT)


@app.get("/users/me/", tags=['Пользователь'])
async def read_users_me(
        current_user: Annotated[ResponseUser, Depends(get_current_active_user)],
) -> ResponseUser:
    return current_user


# Роли
@app.post('/role', tags=['Роли'])
def create_role(data: RoleCreate, session: SessionDep):
    new_role = UsersRoles(
        name_role=data.name_role,
        create=data.create,
        read=data.read,
        update=data.update,
        delete=data.delete
    )

    session.add(new_role)
    session.commit()

    return data


@app.put('/role', tags=["Роли"])
def update_role(data: RoleUpdate, session: SessionDep):
    get_role = session.scalars(select(UsersRoles).where(UsersRoles.name_role == data.name_role)).one_or_none()

    if get_role is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Роль не была найдена")

    get_role.create = data.create
    get_role.read = data.read
    get_role.update = data.update
    get_role.delete = data.delete
    session.commit()

    return data


# Посты

@app.post("/posts", tags=["Посты"])
def create_post(data: CreatePost, current_user: Annotated[ResponseUser, Depends(get_current_active_user)],
                session: SessionDep):
    user = current_user
    if not user.role.create:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)
    new_post = Posts(
        article=data.article,
        heading=data.heading
    )
    session.add(new_post)
    session.commit()
    return data


@app.get("/posts", tags=["Посты"])
def read_posts(limit: int, current_user: Annotated[ResponseUser, Depends(get_current_active_user)],
               session: SessionDep):
    user = current_user
    if not user.role.read:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)
    posts = session.scalars(select(Posts).order_by(desc(Posts.id)).limit(limit)).all()
    print(posts)
    return posts


@app.put("/posts", tags=["Посты"])
def update_post(data: UpdatePost, current_user: Annotated[ResponseUser, Depends(get_current_active_user)],
                session: SessionDep):
    user = current_user
    if not user.role.update:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)
    post = session.get(Posts, data.id)
    if post is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    post.heading = data.heading
    post.article = data.article
    session.commit()
    return data


@app.delete("/posts", tags=["Посты"])
def delete_post(post_id: int, current_user: Annotated[ResponseUser, Depends(get_current_active_user)],
                session: SessionDep):
    user = current_user
    if not user.role.delete:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)
    post = session.get(Posts, post_id)
    if post is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    session.delete(post)
    session.commit()
    return HTTPException(status_code=status.HTTP_204_NO_CONTENT)