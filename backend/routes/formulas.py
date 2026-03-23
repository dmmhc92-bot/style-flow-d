from fastapi import APIRouter, Depends, HTTPException
from typing import List, Optional
from datetime import datetime
from bson import ObjectId

from core.database import db
from core.dependencies import get_current_user
from models.formula import FormulaCreate, FormulaResponse

router = APIRouter(prefix="/formulas", tags=["Formulas"])

@router.post("", response_model=FormulaResponse)
async def create_formula(formula_data: FormulaCreate, current_user: dict = Depends(get_current_user)):
    user_id = str(current_user["_id"])
    
    formula_doc = {
        "user_id": user_id,
        "client_id": formula_data.client_id,
        "formula_name": formula_data.formula_name,
        "formula_details": formula_data.formula_details,
        "date_created": formula_data.date_created or datetime.utcnow()
    }
    
    result = await db.formulas.insert_one(formula_doc)
    formula_doc["id"] = str(result.inserted_id)
    
    return FormulaResponse(**formula_doc)

@router.get("", response_model=List[FormulaResponse])
async def get_formulas(client_id: Optional[str] = None, current_user: dict = Depends(get_current_user)):
    user_id = str(current_user["_id"])
    query = {"user_id": user_id}
    if client_id:
        query["client_id"] = client_id
    
    formulas = await db.formulas.find(query).to_list(1000)
    return [FormulaResponse(id=str(f["_id"]), **{k: v for k, v in f.items() if k != "_id"}) for f in formulas]

@router.get("/{formula_id}", response_model=FormulaResponse)
async def get_formula(formula_id: str, current_user: dict = Depends(get_current_user)):
    """Get a single formula by ID"""
    try:
        formula = await db.formulas.find_one({
            "_id": ObjectId(formula_id),
            "user_id": str(current_user["_id"])
        })
    except:
        raise HTTPException(status_code=404, detail="Formula not found")
    
    if not formula:
        raise HTTPException(status_code=404, detail="Formula not found")
    
    return FormulaResponse(id=str(formula["_id"]), **{k: v for k, v in formula.items() if k != "_id"})

@router.put("/{formula_id}")
async def update_formula(formula_id: str, formula_data: dict, current_user: dict = Depends(get_current_user)):
    try:
        result = await db.formulas.update_one(
            {"_id": ObjectId(formula_id), "user_id": str(current_user["_id"])},
            {"$set": formula_data}
        )
    except:
        raise HTTPException(status_code=404, detail="Formula not found")
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Formula not found")
    
    # Return the updated formula for immediate UI sync
    updated_formula = await db.formulas.find_one({"_id": ObjectId(formula_id)})
    return {
        "id": str(updated_formula["_id"]),
        **{k: v for k, v in updated_formula.items() if k != "_id"}
    }

@router.delete("/{formula_id}")
async def delete_formula(formula_id: str, current_user: dict = Depends(get_current_user)):
    try:
        result = await db.formulas.delete_one({"_id": ObjectId(formula_id), "user_id": str(current_user["_id"])})
    except:
        raise HTTPException(status_code=404, detail="Formula not found")
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Formula not found")
    
    return {"message": "Formula deleted successfully"}
