from datetime import timedelta
from typing import Optional
from fastapi import HTTPException, status
from prisma.models import User, CorporateProfile
from prisma.enums import Role
from app.db import db
from app.utils.security import verify_password, get_password_hash, create_access_token
from app.auth.schemas import UserLogin, CorporateRegister, StudentRegister, Token
from app.config import settings

class AuthService:
    async def authenticate_user(self, login_data: UserLogin) -> Optional[User]:
        user = await db.user.find_unique(where={"email": login_data.email})
        if not user:
            return None
        if not verify_password(login_data.password, user.password):
            return None
        return user

    async def register_corporate(self, data: CorporateRegister) -> User:
        # Check if email exists
        existing_user = await db.user.find_unique(where={"email": data.email})
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        
        # Transactional create (Prisma supports nested writes)
        # We need to create User AND CorporateProfile
        hashed_pw = get_password_hash(data.password)
        
        user = await db.user.create(
            data={
                "name": data.name,
                "email": data.email,
                "password": hashed_pw,
                "role": Role.CORPORATE,
                "corporate_profile": {
                    "create": {
                        "company_name": data.company_name,
                        "hr_name": data.hr_name,
                        "email": data.email 
                    }
                }
            },
            include={"corporate_profile": True}
        )
        return user

    async def register_student(self, data: StudentRegister) -> User:
        # Check if email exists
        existing_user = await db.user.find_unique(where={"email": data.email})
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        
        hashed_pw = get_password_hash(data.password)
        
        # Create User with optional department connection
        # Note: department_id is passed as a direct field if schema allows, 
        # or we might need to connect it relationally
        
        # Based on my schema update: department_id String?
        # So we can pass department_id directly if using raw create, 
        # but Prisma python might prefer nested connect for relations.
        # However, since I added department_id as a scalar field too, it should work.
        
        user = await db.user.create(
            data={
                "name": data.name,
                "email": data.email,
                "password": hashed_pw,
                "role": Role.STUDENT,
                "department_id": data.department_id
            },
            include={"department": True}
        )
        return user

    def create_token_for_user(self, user: User) -> Token:
        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": user.id, "role": user.role},
            expires_delta=access_token_expires
        )
        return Token(access_token=access_token, token_type="bearer")

auth_service = AuthService()
