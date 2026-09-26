from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger
from sqlalchemy import text

from app.config import settings
from app.database.session import engine
from app.routers import alumni, auth, career_advisor, events, financial_aid, jobs, surveys


@asynccontextmanager
async def lifespan(app: FastAPI):
    # --- STARTUP ---
    try:
        from app.database.models import Base

        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("Database tables verified/created successfully.")

        # Auto-seed DLU sample data if empty
        from app.database.seed_data import seed_dlu_data
        from app.database.session import async_session_factory

        async with async_session_factory() as session:
            await seed_dlu_data(session)
    except Exception as e:
        logger.error(f"Database initialization or seed error: {e}")

    yield

    # --- SHUTDOWN ---
    await engine.dispose()
    logger.info("Application shutdown complete.")


app = FastAPI(
    title="Alumni Portal API",
    description="Cổng thông tin Quản lý & Kết nối Cựu sinh viên - Khoa CNTT",
    version="1.0.0",
    lifespan=lifespan,
)

# --- CORS ---
logger.info(f"Allowed CORS origins: {settings.cors_origin_list}")
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Mount Routers ---
app.include_router(auth.router, prefix="/api")
app.include_router(alumni.router, prefix="/api")
app.include_router(jobs.router, prefix="/api")
app.include_router(events.router, prefix="/api")
app.include_router(surveys.router, prefix="/api")
app.include_router(financial_aid.router, prefix="/api")
app.include_router(career_advisor.router, prefix="/api")


@app.get("/")
async def root():
    return {
        "name": "Alumni Portal API",
        "status": "online",
        "version": "1.0.0",
        "docs": "/docs",
    }
