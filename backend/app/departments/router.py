from fastapi import APIRouter, Depends
from app.db import db
from app.auth.dependencies import get_current_user
from prisma.models import User

router = APIRouter(prefix="/departments", tags=["Departments"])

@router.get("")
async def list_departments(current_user: User = Depends(get_current_user)):
    return await db.department.find_many(order={"name": "asc"})

from pydantic import BaseModel
from app.auth.dependencies import require_role
from prisma.enums import Role

class DepartmentCreate(BaseModel):
    name: str

@router.post("")
async def create_department(
    data: DepartmentCreate,
    current_user: User = Depends(require_role(Role.ADMIN))
):
    return await db.department.create(data={"name": data.name})

@router.delete("/{id}")
async def delete_department(
    id: str,
    current_user: User = Depends(require_role(Role.ADMIN))
):
    await db.department.delete(where={"id": id})
    return {"message": "Deleted"}
