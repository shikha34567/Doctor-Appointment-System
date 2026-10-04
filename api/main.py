import os
import sys
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from api.routes.auth import router as auth_router
from api.routes.doctors import router as doctors_router
from api.routes.appointments import router as appointments_router
from api.routes.operations import router as operations_router
from api.routes.reports import router as reports_router
from database.init_db import init_database

load_dotenv()

app = FastAPI(
    title="Hospital Resource & Patient Flow Optimization API",
    description=(
        "REST API backend for Hospital Operations Management, Patient Flow Optimization, "
        "and Healthcare Resource Decision Support. Provides real-time bed tracking, "
        "admission forecasting, emergency waiting-time analytics, and scenario simulation."
    ),
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Routers
app.include_router(auth_router, prefix="/api/v1")
app.include_router(doctors_router, prefix="/api/v1")
app.include_router(appointments_router, prefix="/api/v1")
app.include_router(operations_router, prefix="/api/v1")
app.include_router(reports_router, prefix="/api/v1")


@app.on_event("startup")
def on_startup():
    # Ensure database tables and initial registries are ready
    try:
        init_database()
    except Exception as e:
        print(f"Startup notice: Database initialization checked ({e})")


@app.get("/", tags=["Health"])
def root_status():
    return {
        "system": "Hospital Resource & Patient Flow Optimization System",
        "status": "Online",
        "version": "2.0.0",
        "api_docs": "/docs",
        "lineage": "Multi-Role RBAC & ML Operations Engine"
    }


if __name__ == "__main__":
    import uvicorn
    host = os.getenv("API_HOST", "127.0.0.1")
    port = int(os.getenv("API_PORT", "8000"))
    uvicorn.run("api.main:app", host=host, port=port, reload=True)
