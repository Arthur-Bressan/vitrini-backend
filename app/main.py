from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.catalogos import router as catalogos_router
from app.api.health import router as health_router
from app.config import settings
from app.database import Base, engine

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Catalogo API")
configured_origins = [
    origin.strip().rstrip("/")
    for origin in [settings.frontend_url, *settings.cors_origins.split(",")]
    if origin.strip()
]
allowed_origins = list(dict.fromkeys([
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:3001",
    "http://127.0.0.1:3001",
    "http://0.0.0.0:3000",
    *configured_origins,
]))
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_origin_regex=r"https://[a-zA-Z0-9-]+\.vercel\.app",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(health_router)
app.include_router(catalogos_router)


@app.get("/")
def root() -> dict[str, str]:
    return {"message": "catalogo-api"}
