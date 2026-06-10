from pydantic import BaseModel, EmailStr, SecretStr


# Токены

class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    user_id: int | None = None


# Пользователи

class ResponseUser(BaseModel):
    email: EmailStr

    class Config:
        from_attributes = True


class Login(BaseModel):
    email: EmailStr
    password: SecretStr


class SignUp(Login):
    fullname: str
    repeat_password: SecretStr
    role: str


class UserUpdate(BaseModel):
    email: EmailStr | None = None
    fullname: str | None = None
    password: SecretStr | None = None
    new_password: SecretStr | None = None
    repeat_password: SecretStr | None = None


# Роли

class RoleBase(BaseModel):
    name_role: str


class RoleCreate(RoleBase):
    create: bool = False
    read: bool = False
    update: bool = False
    delete: bool = False


class RoleUpdate(RoleBase):
    create: bool = False
    read: bool = False
    update: bool = False
    delete: bool = False


# Посты

class CreatePost(BaseModel):
    heading: str
    article: str

class UpdatePost(CreatePost):
    id: int
