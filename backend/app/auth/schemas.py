from pydantic import BaseModel, EmailStr
from typing import Optional
from prisma.enums import Role

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    user_id: Optional[str] = None
    role: Optional[Role] = None

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class CorporateRegister(BaseModel):
    name: str
    email: EmailStr
    password: str
    company_name: str
    company_name: str
    hr_name: str

class StudentRegister(BaseModel):
    name: str
    email: EmailStr
    password: str
    department_id: str

class UserResponse(BaseModel):
    id: str
    name: str
    email: EmailStr
    role: Role
    
    class Config:
        from_attributes = True
