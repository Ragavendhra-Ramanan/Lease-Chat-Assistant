from pydantic import BaseModel

class User(BaseModel):
  firstName: str
  lastName: str
  email: str
  mobile: str
  password: str
  country: str

class Login(BaseModel):
  userName: str
  password: str


class SignupResponse(BaseModel):
  value: bool

class LoginResponse(BaseModel):
  userId : str