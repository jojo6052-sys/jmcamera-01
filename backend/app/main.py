from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import engine
from app.models.base import Base
from app.routers import analytics_router, candidates_router, competitors_router, ebay_compliance_router, feedbacks_router, imports_router, phase_router, search_keywords_router, yahoo_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(title=settings.app_name, lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok", "service": settings.app_name}


@app.get(f"{settings.api_prefix}/health")
def api_health_check() -> dict[str, str]:
    return {"status": "ok"}

app.include_router(imports_router)
app.include_router(phase_router)
app.include_router(analytics_router)
app.include_router(search_keywords_router)
app.include_router(yahoo_router)
app.include_router(feedbacks_router)
app.include_router(candidates_router)
app.include_router(competitors_router)
app.include_router(ebay_compliance_router)
