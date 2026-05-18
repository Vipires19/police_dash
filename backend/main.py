from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from core.config import settings
from database.session import SessionLocal
from routes import auth as auth_routes
from routes import compensations as compensations_routes
from routes import leaves as leaves_routes
from routes import users as users_routes
from routes import vacations as vacations_routes
from routes import vehicles as vehicles_routes
from routes import service_scales as service_scales_routes
from services.user_service import ensure_bootstrap_admin


@asynccontextmanager
async def lifespan(_: FastAPI):
    db = SessionLocal()
    try:
        if settings.admin_email and settings.admin_password:
            ensure_bootstrap_admin(
                db,
                settings.admin_email,
                settings.admin_password,
                settings.admin_patente,
                settings.admin_nome_guerra,
            )
    finally:
        db.close()
    yield


app = FastAPI(title="Pelotão System API", lifespan=lifespan)

origins = [o.strip() for o in settings.cors_origins.split(",") if o.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_routes.router)
app.include_router(users_routes.router)
app.include_router(vehicles_routes.router)
app.include_router(leaves_routes.router)
app.include_router(compensations_routes.router)
app.include_router(vacations_routes.router)
app.include_router(service_scales_routes.router)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
