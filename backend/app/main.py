from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .core.config import settings
from .api.routes import router

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Hệ thống phát hiện gian lận và đánh giá rủi ro giao dịch VietQR dựa trên phân tích ngữ nghĩa EMVCo",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configure CORS
origins = [origin.strip() for origin in settings.ALLOWED_ORIGINS.split(",")]
if "*" in origins:
    origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)

@app.get("/")
def root():
    return {
        "message": "SafeQR-Cloud API is running",
        "docs": "/docs",
        "version": settings.VERSION
    }
