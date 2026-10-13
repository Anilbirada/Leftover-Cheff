"""
Leftover Chef — FastAPI Application Entry Point.
Smart Recipe Discovery and Ingredient Matching Platform.
Developed by Anil Biradar.
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.routes import router as api_v1_router
from app.core.config import settings
from app.core.database import Base, SessionLocal, engine
from app.services.seed_service import seed_database_from_file


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    with SessionLocal() as db:
        seed_database_from_file(db)
    yield


app = FastAPI(
    title=f"{settings.app_name} API",
    description=(
        "Smart Recipe Discovery and Ingredient Matching Platform. "
        "Helps users cook with available ingredients, reduce food waste, and scale servings safely. "
        "Developed by Anil Biradar."
    ),
    version=settings.app_version,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)


@app.middleware("http")
async def security_headers_and_size_limit(request: Request, call_next):
    content_length = request.headers.get("content-length")
    if content_length and int(content_length) > settings.max_request_body_bytes:
        return JSONResponse(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            content={"detail": "Request payload exceeds maximum allowed size."},
        )
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    return response


app.include_router(api_v1_router)
