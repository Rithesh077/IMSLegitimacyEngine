from fastapi import APIRouter, Depends
from app.db import db
from app.auth.dependencies import get_current_user
from prisma.models import User

router = APIRouter(prefix="/departments", tags=["Departments"])

@router.get("")
async def list_departments(current_user: User = Depends(get_current_user)):
    return await db.department.find_many(order={"name": "asc"})
