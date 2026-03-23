from fastapi import APIRouter, Depends
from datetime import datetime, timedelta
from bson import ObjectId

from core.database import db
from core.dependencies import get_current_user
from routes.clients import enrich_client_with_rebook

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])

@router.get("/stats")
async def get_dashboard_stats(current_user: dict = Depends(get_current_user)):
    user_id = str(current_user["_id"])
    
    # Get counts - STRICTLY user-scoped
    total_clients = await db.clients.count_documents({"user_id": user_id})
    vip_clients = await db.clients.count_documents({"user_id": user_id, "is_vip": True})
    
    # Today's appointments - STRICTLY user-scoped
    today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    today_end = today_start + timedelta(days=1)
    today_appointments = await db.appointments.count_documents({
        "user_id": user_id,
        "appointment_date": {"$gte": today_start, "$lt": today_end}
    })
    
    # This week's appointments
    week_start = today_start - timedelta(days=today_start.weekday())
    week_appointments = await db.appointments.count_documents({
        "user_id": user_id,
        "appointment_date": {"$gte": week_start}
    })
    
    # Followers count
    followers_count = await db.follows.count_documents({
        "following_id": user_id
    })
    
    # New clients this week
    new_clients_this_week = await db.clients.count_documents({
        "user_id": user_id,
        "created_at": {"$gte": week_start}
    })
    
    # SMART REBOOK: Calculate clients due/overdue using per-client intervals
    clients = await db.clients.find({"user_id": user_id}).to_list(1000)
    clients_due_soon = 0
    clients_overdue = 0
    
    for c in clients:
        enriched = enrich_client_with_rebook(c)
        if enriched.get("rebook_status") == "due_soon":
            clients_due_soon += 1
        elif enriched.get("rebook_status") == "overdue":
            clients_overdue += 1
    
    return {
        "total_clients": total_clients,
        "vip_clients": vip_clients,
        "today_appointments": today_appointments,
        "week_appointments": week_appointments,
        "followers_count": followers_count,
        "new_clients_this_week": new_clients_this_week,
        "clients_due_rebooking": clients_due_soon + clients_overdue,
        "clients_due_soon": clients_due_soon,
        "clients_overdue": clients_overdue
    }
