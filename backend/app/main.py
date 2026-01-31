from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from app.db import connect_db, disconnect_db
from app.auth.router import router as auth_router
from app.internships.router import router as internships_router
from app.approvals.router import router as approvals_router

app = FastAPI(title="Internship Management System")

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from app.departments.router import router as departments_router

# API Routers
app.include_router(auth_router)
app.include_router(internships_router)
app.include_router(approvals_router)
app.include_router(departments_router)

from app.admin.router import router as admin_router
app.include_router(admin_router)

import os

# Create uploads directory if it doesn't exist
if not os.path.exists("uploads"):
    os.makedirs("uploads")

# Mount Frontend
try:
    app.mount("/ui", StaticFiles(directory="frontend-test", html=True), name="ui")
except RuntimeError:
    print("Frontend directory not found, skipping mount.")

# Mount Uploads
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

@app.on_event("startup")
async def startup():
    await connect_db()

@app.on_event("shutdown")
async def shutdown():
    await disconnect_db()

@app.get("/")
async def root():
    return {"message": "Welcome to the Internship Management System API"}
