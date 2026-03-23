# Routes module
from fastapi import APIRouter

# Create routers for each module
auth_router = APIRouter(prefix="/auth", tags=["Authentication"])
users_router = APIRouter(prefix="/users", tags=["Users"])
clients_router = APIRouter(prefix="/clients", tags=["Clients"])
formulas_router = APIRouter(prefix="/formulas", tags=["Formulas"])
appointments_router = APIRouter(prefix="/appointments", tags=["Appointments"])
gallery_router = APIRouter(prefix="/gallery", tags=["Gallery"])
income_router = APIRouter(prefix="/income", tags=["Income"])
retail_router = APIRouter(prefix="/retail", tags=["Retail"])
noshows_router = APIRouter(prefix="/no-shows", tags=["No-Shows"])
posts_router = APIRouter(prefix="/posts", tags=["Posts"])
admin_router = APIRouter(prefix="/admin", tags=["Admin"])
ai_router = APIRouter(prefix="/ai", tags=["AI"])
dashboard_router = APIRouter(prefix="/dashboard", tags=["Dashboard"])
misc_router = APIRouter(tags=["Misc"])
