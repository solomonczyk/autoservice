from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.api.api import api_router

from contextlib import asynccontextmanager
from app.bot.loader import dp, bot
from app.bot.handlers import router as bot_router

import logging
import sys
import asyncio

logging.basicConfig(level=logging.DEBUG)
logging.getLogger("aiogram").setLevel(logging.DEBUG)
logger = logging.getLogger(__name__)

if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Lifespan startup initiated")
    yield
    # Shutdown
    logger.info("Lifespan shutdown initiated")
    # Shutdown
    # await bot.session.close()

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    lifespan=lifespan
)

# Set all CORS enabled origins
if settings.BACKEND_CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[str(origin) for origin in settings.BACKEND_CORS_ORIGINS],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
else:
    # Fallback/Dev defaults
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:5173", "http://localhost:5174", "http://localhost:3000"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

app.include_router(api_router, prefix=settings.API_V1_STR)

@app.middleware("http")
async def log_requests(request, call_next):
    logger.debug(f"Incoming request: {request.method} {request.url.path}")
    logger.debug(f"Headers: {request.headers.get('authorization', 'No Auth Header')[:20]}...")
    response = await call_next(request)
    logger.debug(f"Response status: {response.status_code}")
    return response

@app.get("/health")
async def health_check():
    return {"status": "ok", "project": settings.PROJECT_NAME}

@app.get("/")
async def root():
    return {"message": "Welcome to Autoservice API"}
