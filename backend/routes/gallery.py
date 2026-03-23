from fastapi import APIRouter, Depends, HTTPException
from typing import List, Optional
from datetime import datetime
from bson import ObjectId

from core.database import db
from core.dependencies import get_current_user
from models.gallery import GalleryCreate, GalleryResponse

router = APIRouter(prefix="/gallery", tags=["Gallery"])

@router.post("", response_model=GalleryResponse)
async def create_gallery(gallery_data: GalleryCreate, current_user: dict = Depends(get_current_user)):
    user_id = str(current_user["_id"])
    
    gallery_doc = {
        "user_id": user_id,
        "client_id": gallery_data.client_id,
        "before_photo": gallery_data.before_photo,
        "after_photo": gallery_data.after_photo,
        "notes": gallery_data.notes,
        "date_taken": gallery_data.date_taken or datetime.utcnow()
    }
    
    result = await db.gallery.insert_one(gallery_doc)
    gallery_doc["id"] = str(result.inserted_id)
    
    return GalleryResponse(**gallery_doc)

@router.get("", response_model=List[GalleryResponse])
async def get_gallery(client_id: Optional[str] = None, current_user: dict = Depends(get_current_user)):
    user_id = str(current_user["_id"])
    query = {"user_id": user_id}
    if client_id:
        query["client_id"] = client_id
    
    gallery = await db.gallery.find(query).sort("date_taken", -1).to_list(1000)
    return [GalleryResponse(id=str(g["_id"]), **{k: v for k, v in g.items() if k != "_id"}) for g in gallery]

@router.delete("/{gallery_id}")
async def delete_gallery(gallery_id: str, current_user: dict = Depends(get_current_user)):
    try:
        result = await db.gallery.delete_one({"_id": ObjectId(gallery_id), "user_id": str(current_user["_id"])})
    except:
        raise HTTPException(status_code=404, detail="Gallery item not found")
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Gallery item not found")
    
    return {"message": "Gallery item deleted successfully"}
