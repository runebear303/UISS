from app.database.db import engine, Base
from fastapi import Depends
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
from app.api.routes import router
from app.services.monitor import system_stats
from app.services.dependencies import verify_admin
from app.config import ENV

# ===============================
# LIFESPAN (Startup / Shutdown)
# ===============================

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create all tables if they don't exist
    Base.metadata.create_all(bind=engine)
    
    print(f"Running in {ENV} mode")
    yield
    print("Shutting down application")

app = FastAPI(
    title="UNASAT Intelligent Support System (UISS)",
    version="1.0.0",
    lifespan=lifespan
)

# ===============================
# CORS CONFIGURATION
# ===============================

if ENV == "production":
    origins = ["https://your-frontend-domain.com"]
else:
    origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ===============================
# GLOBAL ERROR HANDLER
# ===============================

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )

# ===============================
# ROUTES
# ===============================

app.include_router(router, prefix="/api")

# ===============================
# BASIC HEALTH CHECK
# ===============================

@app.get("/")
def health():
    return {
        "status": "running",
        "environment": ENV
    }

# ===============================
# SYSTEM HEALTH (ADMIN ONLY)
# ===============================

@app.get("/health/system")
def system_health(user=Depends(verify_admin)):
    return {
        "status": "running",
        "environment": ENV,
        "system": system_stats()
    }
