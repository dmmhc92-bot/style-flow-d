from fastapi import APIRouter, Depends, HTTPException
from typing import List
from datetime import datetime
from bson import ObjectId

from core.database import db
from core.dependencies import get_current_user
from models.appointment import AppointmentCreate, AppointmentResponse

router = APIRouter(prefix="/appointments", tags=["Appointments"])

@router.post("", response_model=AppointmentResponse)
async def create_appointment(appointment_data: AppointmentCreate, current_user: dict = Depends(get_current_user)):
    user_id = str(current_user["_id"])
    
    appointment_doc = {
        "user_id": user_id,
        "client_id": appointment_data.client_id,
        "appointment_date": appointment_data.appointment_date,
        "service": appointment_data.service,
        "duration_minutes": appointment_data.duration_minutes,
        "notes": appointment_data.notes,
        "status": appointment_data.status
    }
    
    result = await db.appointments.insert_one(appointment_doc)
    appointment_doc["id"] = str(result.inserted_id)
    
    # Get client name
    try:
        client = await db.clients.find_one({"_id": ObjectId(appointment_data.client_id)})
        appointment_doc["client_name"] = client["name"] if client else None
    except:
        appointment_doc["client_name"] = None
    
    return AppointmentResponse(**appointment_doc)

@router.get("/{appointment_id}")
async def get_single_appointment(appointment_id: str, current_user: dict = Depends(get_current_user)):
    """Get a single appointment by ID"""
    try:
        appointment = await db.appointments.find_one({
            "_id": ObjectId(appointment_id), 
            "user_id": str(current_user["_id"])
        })
    except:
        raise HTTPException(status_code=404, detail="Appointment not found")
    
    if not appointment:
        raise HTTPException(status_code=404, detail="Appointment not found")
    
    # Enrich with client name
    try:
        client = await db.clients.find_one({"_id": ObjectId(appointment["client_id"])})
        appointment["client_name"] = client["name"] if client else None
    except:
        appointment["client_name"] = None
    
    return {
        "id": str(appointment["_id"]),
        **{k: v for k, v in appointment.items() if k != "_id"}
    }

@router.get("", response_model=List[AppointmentResponse])
async def get_appointments(current_user: dict = Depends(get_current_user)):
    user_id = str(current_user["_id"])
    appointments = await db.appointments.find({"user_id": user_id}).sort("appointment_date", 1).to_list(1000)
    
    # Enrich with client names
    result = []
    for apt in appointments:
        try:
            client = await db.clients.find_one({"_id": ObjectId(apt["client_id"])})
            apt["client_name"] = client["name"] if client else None
        except:
            apt["client_name"] = None
        
        result.append(AppointmentResponse(id=str(apt["_id"]), **{k: v for k, v in apt.items() if k != "_id"}))
    
    return result

@router.put("/{appointment_id}")
async def update_appointment(appointment_id: str, appointment_data: dict, current_user: dict = Depends(get_current_user)):
    try:
        result = await db.appointments.update_one(
            {"_id": ObjectId(appointment_id), "user_id": str(current_user["_id"])},
            {"$set": appointment_data}
        )
    except:
        raise HTTPException(status_code=404, detail="Appointment not found")
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Appointment not found")
    
    # If status changed to completed, update client visit count
    if appointment_data.get("status") == "completed":
        appointment = await db.appointments.find_one({"_id": ObjectId(appointment_id)})
        if appointment:
            await db.clients.update_one(
                {"_id": ObjectId(appointment["client_id"])},
                {
                    "$inc": {"visit_count": 1},
                    "$set": {"last_visit": datetime.utcnow()}
                }
            )
    
    # Return the updated appointment for immediate UI sync
    updated_appointment = await db.appointments.find_one({"_id": ObjectId(appointment_id)})
    
    # Enrich with client name
    try:
        client = await db.clients.find_one({"_id": ObjectId(updated_appointment["client_id"])})
        updated_appointment["client_name"] = client["name"] if client else None
    except:
        updated_appointment["client_name"] = None
    
    return {
        "id": str(updated_appointment["_id"]),
        **{k: v for k, v in updated_appointment.items() if k != "_id"}
    }

@router.delete("/{appointment_id}")
async def delete_appointment(appointment_id: str, current_user: dict = Depends(get_current_user)):
    try:
        result = await db.appointments.delete_one({"_id": ObjectId(appointment_id), "user_id": str(current_user["_id"])})
    except:
        raise HTTPException(status_code=404, detail="Appointment not found")
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Appointment not found")
    
    return {"message": "Appointment deleted successfully"}
