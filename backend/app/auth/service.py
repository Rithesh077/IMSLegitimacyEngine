from datetime import timedelta
from typing import Optional
from fastapi import HTTPException, status
from prisma.models import User, CorporateProfile
from prisma.enums import Role
from app.db import db
from app.utils.security import verify_password, get_password_hash, create_access_token
from app.auth.schemas import UserLogin, CorporateRegister, Token
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
        # check email exists
        existing_user = await db.user.find_unique(where={"email": data.email})
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        
        # verification pipeline
        # running this before saving to db
        from app.engine.pipeline_orchestrator import PipelineOrchestrator
        from app.schemas.company import CompanyInput
        import json

        orchestrator = PipelineOrchestrator()
        
        # map input data
        pipeline_input = CompanyInput(
            name=data.company_name,
            country=data.country,
            registry_id=data.registry_number,
            website=data.website_url,
            linkedin=data.linkedin_url
        )
        
        # run pipeline
        analysis_result = await orchestrator.run_pipeline(pipeline_input)
        
        # convert to json
        report_json = json.loads(analysis_result.model_dump_json())

        # creating user and profile
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
                        "email": data.email,
                        "country": data.country,
                        "registration_number": data.registry_number,
                        "website_url": data.website_url,
                        "linkedin_url": data.linkedin_url,
                        
                        # core integration point
                        # admin dashboard flags unverified status
                        # stored in: user.corporate_profile.verification_report
                        "verification_report": report_json,
                    }
                }
            },
            include={"corporate_profile": True}
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
