from pydantic import BaseModel, EmailStr, SecretStr


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    email: str | None = None


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


class UserUpdate(BaseModel):
    email: EmailStr | None = None
    fullname: str | None = None
    password: SecretStr | None = None
    new_password: SecretStr | None = None
    repeat_password: SecretStr | None = None
