from fastapi import FastAPI

from app.config import settings
from app.database import engine
from app.models.base import Base

from app.routers import analytics_router, imports_router


app = FastAPI(title=settings.app_name)


@app.on_event("startup")
def startup() -> None:
    Base.metadata.create_all(bind=engine)


@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok", "service": settings.app_name}


@app.get(f"{settings.api_prefix}/health")
def api_health_check() -> dict[str, str]:
    return {"status": "ok"}


app.include_router(imports_router)
app.include_router(analytics_router)

