from fastapi import APIRouter, Depends, HTTPException
from typing import List
from datetime import datetime, timedelta
from bson import ObjectId

from core.database import db
from core.dependencies import get_current_user
from models.business import (
    IncomeCreate, IncomeResponse,
    RetailCreate, RetailResponse,
    NoShowCreate, NoShowResponse
)

router = APIRouter(tags=["Business"])

# ==================== INCOME ENDPOINTS ====================

@router.post("/income", response_model=IncomeResponse)
async def create_income(income_data: IncomeCreate, current_user: dict = Depends(get_current_user)):
    user_id = str(current_user["_id"])
    
    income_doc = {
        "user_id": user_id,
        "client_id": income_data.client_id,
        "amount": income_data.amount,
        "service": income_data.service,
        "date": income_data.date or datetime.utcnow(),
        "payment_method": income_data.payment_method
    }
    
    result = await db.income.insert_one(income_doc)
    income_doc["id"] = str(result.inserted_id)
    
    # Get client name
    if income_data.client_id:
        try:
            client = await db.clients.find_one({"_id": ObjectId(income_data.client_id)})
            income_doc["client_name"] = client["name"] if client else None
        except:
            income_doc["client_name"] = None
    else:
        income_doc["client_name"] = None
    
    return IncomeResponse(**income_doc)

@router.get("/income", response_model=List[IncomeResponse])
async def get_income(current_user: dict = Depends(get_current_user)):
    user_id = str(current_user["_id"])
    income = await db.income.find({"user_id": user_id}).sort("date", -1).to_list(1000)
    
    # Enrich with client names
    result = []
    for inc in income:
        if inc.get("client_id"):
            try:
                client = await db.clients.find_one({"_id": ObjectId(inc["client_id"])})
                inc["client_name"] = client["name"] if client else None
            except:
                inc["client_name"] = None
        else:
            inc["client_name"] = None
        
        result.append(IncomeResponse(id=str(inc["_id"]), **{k: v for k, v in inc.items() if k != "_id"}))
    
    return result

@router.get("/income/stats")
async def get_income_stats(current_user: dict = Depends(get_current_user)):
    user_id = str(current_user["_id"])
    
    # Get all income records
    income = await db.income.find({"user_id": user_id}).to_list(1000)
    
    # Calculate stats
    total = sum(i["amount"] for i in income)
    
    # Today
    today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    today_income = sum(i["amount"] for i in income if i["date"] >= today_start)
    
    # This week
    week_start = today_start - timedelta(days=today_start.weekday())
    week_income = sum(i["amount"] for i in income if i["date"] >= week_start)
    
    # This month
    month_start = today_start.replace(day=1)
    month_income = sum(i["amount"] for i in income if i["date"] >= month_start)
    
    return {
        "total": total,
        "today": today_income,
        "week": week_income,
        "month": month_income
    }

# ==================== RETAIL ENDPOINTS ====================

@router.post("/retail", response_model=RetailResponse)
async def create_retail(retail_data: RetailCreate, current_user: dict = Depends(get_current_user)):
    user_id = str(current_user["_id"])
    
    retail_doc = {
        "user_id": user_id,
        "client_id": retail_data.client_id,
        "product_name": retail_data.product_name,
        "recommended": retail_data.recommended,
        "purchased": retail_data.purchased,
        "date": retail_data.date or datetime.utcnow()
    }
    
    result = await db.retail.insert_one(retail_doc)
    retail_doc["id"] = str(result.inserted_id)
    
    # Get client name
    try:
        client = await db.clients.find_one({"_id": ObjectId(retail_data.client_id)})
        retail_doc["client_name"] = client["name"] if client else None
    except:
        retail_doc["client_name"] = None
    
    return RetailResponse(**retail_doc)

@router.get("/retail", response_model=List[RetailResponse])
async def get_retail(current_user: dict = Depends(get_current_user)):
    user_id = str(current_user["_id"])
    retail = await db.retail.find({"user_id": user_id}).sort("date", -1).to_list(1000)
    
    # Enrich with client names
    result = []
    for ret in retail:
        try:
            client = await db.clients.find_one({"_id": ObjectId(ret["client_id"])})
            ret["client_name"] = client["name"] if client else None
        except:
            ret["client_name"] = None
        
        result.append(RetailResponse(id=str(ret["_id"]), **{k: v for k, v in ret.items() if k != "_id"}))
    
    return result

@router.delete("/retail/{retail_id}")
async def delete_retail(retail_id: str, current_user: dict = Depends(get_current_user)):
    try:
        result = await db.retail.delete_one({"_id": ObjectId(retail_id), "user_id": str(current_user["_id"])})
    except:
        raise HTTPException(status_code=404, detail="Retail record not found")
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Retail record not found")
    
    return {"message": "Retail record deleted successfully"}

# ==================== NO-SHOW ENDPOINTS ====================

@router.post("/no-shows", response_model=NoShowResponse)
async def create_no_show(no_show_data: NoShowCreate, current_user: dict = Depends(get_current_user)):
    user_id = str(current_user["_id"])
    
    no_show_doc = {
        "user_id": user_id,
        "client_id": no_show_data.client_id,
        "appointment_date": no_show_data.appointment_date,
        "notes": no_show_data.notes,
        "created_at": datetime.utcnow()
    }
    
    result = await db.no_shows.insert_one(no_show_doc)
    no_show_doc["id"] = str(result.inserted_id)
    
    # Get client name
    try:
        client = await db.clients.find_one({"_id": ObjectId(no_show_data.client_id)})
        no_show_doc["client_name"] = client["name"] if client else None
    except:
        no_show_doc["client_name"] = None
    
    return NoShowResponse(**no_show_doc)

@router.get("/no-shows", response_model=List[NoShowResponse])
async def get_no_shows(current_user: dict = Depends(get_current_user)):
    user_id = str(current_user["_id"])
    no_shows = await db.no_shows.find({"user_id": user_id}).sort("appointment_date", -1).to_list(1000)
    
    # Enrich with client names
    result = []
    for ns in no_shows:
        try:
            client = await db.clients.find_one({"_id": ObjectId(ns["client_id"])})
            ns["client_name"] = client["name"] if client else None
        except:
            ns["client_name"] = None
        
        result.append(NoShowResponse(id=str(ns["_id"]), **{k: v for k, v in ns.items() if k != "_id"}))
    
    return result

@router.delete("/no-shows/{no_show_id}")
async def delete_no_show(no_show_id: str, current_user: dict = Depends(get_current_user)):
    try:
        result = await db.no_shows.delete_one({"_id": ObjectId(no_show_id), "user_id": str(current_user["_id"])})
    except:
        raise HTTPException(status_code=404, detail="No-show record not found")
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="No-show record not found")
    
    return {"message": "No-show record deleted successfully"}
