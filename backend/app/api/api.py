from fastapi import APIRouter
from app.api.endpoints import shops, services, appointments, slots, webhook, ws, login, clients

api_router = APIRouter()

api_router.include_router(login.router, tags=["login"])

api_router.include_router(shops.router, prefix="/shops", tags=["shops"])
api_router.include_router(services.router, prefix="/services", tags=["services"])
api_router.include_router(appointments.router, prefix="/appointments", tags=["appointments"])
api_router.include_router(slots.router, prefix="/slots", tags=["slots"])
api_router.include_router(webhook.router, tags=["telegram"])
api_router.include_router(ws.router, tags=["websocket"])
api_router.include_router(clients.router, prefix="/clients", tags=["clients"])

