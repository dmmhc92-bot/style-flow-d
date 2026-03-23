from fastapi import APIRouter, Depends, HTTPException
from typing import List, Optional
from datetime import datetime, timedelta
from bson import ObjectId

from core.database import db
from core.dependencies import get_current_user
from models.client import ClientCreate, ClientResponse

router = APIRouter(prefix="/clients", tags=["Clients"])

# ==================== REBOOK STATUS HELPER ====================

def calculate_rebook_status(last_visit: Optional[datetime], rebook_interval_days: int = 42) -> dict:
    """Calculate next visit due date and rebook status"""
    if not last_visit:
        return {
            "next_visit_due": None,
            "rebook_status": "new"  # New client, no visit history
        }
    
    next_due = last_visit + timedelta(days=rebook_interval_days)
    now = datetime.utcnow()
    days_until_due = (next_due - now).days
    
    if days_until_due < 0:
        status = "overdue"
    elif days_until_due <= 7:
        status = "due_soon"
    else:
        status = "on_track"
    
    return {
        "next_visit_due": next_due,
        "rebook_status": status
    }

def enrich_client_with_rebook(client: dict) -> dict:
    """Add rebook status fields to client"""
    rebook_interval = client.get("rebook_interval_days", 42)
    last_visit = client.get("last_visit")
    rebook_info = calculate_rebook_status(last_visit, rebook_interval)
    
    return {
        **client,
        "rebook_interval_days": rebook_interval,
        **rebook_info
    }

# ==================== CLIENT ENDPOINTS ====================

@router.post("", response_model=ClientResponse)
async def create_client(client_data: ClientCreate, current_user: dict = Depends(get_current_user)):
    user_id = str(current_user["_id"])
    
    client_doc = {
        "user_id": user_id,
        "name": client_data.name,
        "email": client_data.email,
        "phone": client_data.phone,
        "photo": client_data.photo,
        "notes": client_data.notes,
        "preferences": client_data.preferences,
        "hair_goals": client_data.hair_goals,
        "is_vip": client_data.is_vip,
        "visit_count": 0,
        "last_visit": client_data.last_visit,
        "rebook_interval_days": client_data.rebook_interval_days or 42,
        "created_at": datetime.utcnow()
    }
    
    result = await db.clients.insert_one(client_doc)
    client_doc["id"] = str(result.inserted_id)
    
    # Enrich with rebook status
    enriched = enrich_client_with_rebook(client_doc)
    
    return ClientResponse(**enriched)

@router.get("", response_model=List[ClientResponse])
async def get_clients(current_user: dict = Depends(get_current_user)):
    user_id = str(current_user["_id"])
    clients = await db.clients.find({"user_id": user_id}).to_list(1000)
    
    result = []
    for c in clients:
        enriched = enrich_client_with_rebook(c)
        result.append(ClientResponse(id=str(c["_id"]), **{k: v for k, v in enriched.items() if k != "_id"}))
    
    return result

@router.get("/rebook/due")
async def get_clients_due_for_rebook(current_user: dict = Depends(get_current_user)):
    """Get clients due or overdue for rebooking - STRICTLY user-scoped"""
    user_id = str(current_user["_id"])
    
    clients = await db.clients.find({"user_id": user_id}).to_list(1000)
    
    due_soon = []
    overdue = []
    
    for c in clients:
        enriched = enrich_client_with_rebook(c)
        client_data = {
            "id": str(c["_id"]),
            **{k: v for k, v in enriched.items() if k != "_id"}
        }
        
        if enriched.get("rebook_status") == "due_soon":
            due_soon.append(client_data)
        elif enriched.get("rebook_status") == "overdue":
            overdue.append(client_data)
    
    return {
        "due_soon": due_soon,
        "overdue": overdue,
        "total_due": len(due_soon) + len(overdue)
    }

@router.get("/{client_id}", response_model=ClientResponse)
async def get_client(client_id: str, current_user: dict = Depends(get_current_user)):
    try:
        client = await db.clients.find_one({"_id": ObjectId(client_id), "user_id": str(current_user["_id"])})
    except:
        raise HTTPException(status_code=404, detail="Client not found")
    
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    
    enriched = enrich_client_with_rebook(client)
    return ClientResponse(id=str(client["_id"]), **{k: v for k, v in enriched.items() if k != "_id"})

@router.put("/{client_id}")
async def update_client(client_id: str, client_data: dict, current_user: dict = Depends(get_current_user)):
    try:
        result = await db.clients.update_one(
            {"_id": ObjectId(client_id), "user_id": str(current_user["_id"])},
            {"$set": client_data}
        )
    except:
        raise HTTPException(status_code=404, detail="Client not found")
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Client not found")
    
    # Return the updated client with rebook status for immediate UI sync
    updated_client = await db.clients.find_one({"_id": ObjectId(client_id)})
    enriched = enrich_client_with_rebook(updated_client)
    return {
        "id": str(updated_client["_id"]),
        **{k: v for k, v in enriched.items() if k != "_id"}
    }

@router.delete("/{client_id}")
async def delete_client(client_id: str, current_user: dict = Depends(get_current_user)):
    try:
        result = await db.clients.delete_one({"_id": ObjectId(client_id), "user_id": str(current_user["_id"])})
    except:
        raise HTTPException(status_code=404, detail="Client not found")
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Client not found")
    
    # Delete related data - STRICTLY USER-SCOPED
    user_id = str(current_user["_id"])
    await db.formulas.delete_many({"client_id": client_id, "user_id": user_id})
    await db.gallery.delete_many({"client_id": client_id, "user_id": user_id})
    await db.appointments.delete_many({"client_id": client_id, "user_id": user_id})
    await db.retail.delete_many({"client_id": client_id, "user_id": user_id})
    await db.no_shows.delete_many({"client_id": client_id, "user_id": user_id})
    
    return {"message": "Client deleted successfully"}

# ==================== CLIENT TIMELINE ENDPOINT ====================

@router.get("/{client_id}/timeline")
async def get_client_timeline(client_id: str, current_user: dict = Depends(get_current_user)):
    """Get complete timeline for a client - appointments, formulas, gallery, notes
    STRICTLY user-scoped - only returns data for the authenticated user's client"""
    
    user_id = str(current_user["_id"])
    
    # Verify client belongs to user
    try:
        client = await db.clients.find_one({"_id": ObjectId(client_id), "user_id": user_id})
    except:
        raise HTTPException(status_code=404, detail="Client not found")
    
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    
    # Get all related data - ALL queries include user_id for strict isolation
    appointments = await db.appointments.find({
        "client_id": client_id, 
        "user_id": user_id
    }).sort("appointment_date", -1).to_list(100)
    
    formulas = await db.formulas.find({
        "client_id": client_id, 
        "user_id": user_id
    }).sort("date_created", -1).to_list(100)
    
    gallery = await db.gallery.find({
        "client_id": client_id, 
        "user_id": user_id
    }).sort("date_taken", -1).to_list(100)
    
    # Build timeline events
    timeline = []
    
    for apt in appointments:
        timeline.append({
            "id": str(apt["_id"]),
            "type": "appointment",
            "date": apt["appointment_date"],
            "service": apt["service"],
            "status": apt["status"],
            "notes": apt.get("notes"),
            "duration_minutes": apt.get("duration_minutes", 60)
        })
    
    for formula in formulas:
        timeline.append({
            "id": str(formula["_id"]),
            "type": "formula",
            "date": formula["date_created"],
            "formula_name": formula["formula_name"],
            "formula_details": formula["formula_details"]
        })
    
    for photo in gallery:
        timeline.append({
            "id": str(photo["_id"]),
            "type": "photo",
            "date": photo["date_taken"],
            "before_photo": photo.get("before_photo"),
            "after_photo": photo.get("after_photo"),
            "notes": photo.get("notes")
        })
    
    # Sort by date descending
    timeline.sort(key=lambda x: x["date"], reverse=True)
    
    # Enrich client with rebook status
    enriched_client = enrich_client_with_rebook(client)
    
    # Get last formula for "Repeat Last" functionality
    last_formula = formulas[0] if formulas else None
    
    return {
        "client": {
            "id": str(client["_id"]),
            **{k: v for k, v in enriched_client.items() if k != "_id"}
        },
        "timeline": timeline,
        "last_formula": {
            "id": str(last_formula["_id"]),
            "formula_name": last_formula["formula_name"],
            "formula_details": last_formula["formula_details"],
            "date_created": last_formula["date_created"]
        } if last_formula else None,
        "stats": {
            "total_visits": len([a for a in appointments if a["status"] == "completed"]),
            "total_formulas": len(formulas),
            "total_photos": len(gallery)
        }
    }
