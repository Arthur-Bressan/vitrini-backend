from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.catalogos import router as catalogos_router
from app.api.health import router as health_router
from app.database import Base, engine

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Catalogo API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:3001",
        "http://127.0.0.1:3001",
        "http://0.0.0.0:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(health_router)
app.include_router(catalogos_router)


@app.get("/")
def root() -> dict[str, str]:
    return {"message": "catalogo-api"}
