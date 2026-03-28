from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect
from typing import Optional, Dict
from datetime import datetime, timedelta
from bson import ObjectId
import asyncio
import logging
import jwt

from core.database import db
from core.config import settings
from core.dependencies import get_current_user

from models.moderation import (
    ReportCreate, ModerationAction, AppealCreate, AppealAction,
    REPORT_REASONS, MODERATION_ACTIONS
)

router = APIRouter(tags=["Admin"])

# ==================== WEBSOCKET CONNECTION MANAGER ====================

class AdminConnectionManager:
    """Manages WebSocket connections for admin real-time updates"""
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
    
    async def connect(self, websocket: WebSocket, admin_id: str):
        await websocket.accept()
        self.active_connections[admin_id] = websocket
    
    def disconnect(self, admin_id: str):
        if admin_id in self.active_connections:
            del self.active_connections[admin_id]
    
    async def broadcast_to_admins(self, message: dict):
        """Send message to all connected admins"""
        disconnected = []
        for admin_id, connection in self.active_connections.items():
            try:
                await connection.send_json(message)
            except Exception:
                disconnected.append(admin_id)
        
        for admin_id in disconnected:
            self.disconnect(admin_id)

admin_manager = AdminConnectionManager()

# Helper function
async def check_admin(current_user: dict):
    """Check if user is an admin"""
    if not current_user.get("is_admin", False):
        raise HTTPException(status_code=403, detail="Admin access required")

# ==================== REPORT SYSTEM ====================

@router.post("/report")
async def create_report(report_data: ReportCreate, current_user: dict = Depends(get_current_user)):
    current_user_id = str(current_user["_id"])
    
    if current_user_id == report_data.reported_user_id:
        raise HTTPException(status_code=400, detail="Cannot report yourself")
    
    if report_data.reason not in REPORT_REASONS:
        raise HTTPException(status_code=400, detail="Invalid report reason")
    
    existing = await db.reports.find_one({
        "reporter_id": current_user_id,
        "reported_user_id": report_data.reported_user_id,
        "content_type": report_data.content_type,
        "content_id": report_data.content_id,
        "status": "pending"
    })
    
    if existing:
        raise HTTPException(status_code=400, detail="You have already reported this content")
    
    report_doc = {
        "reporter_id": current_user_id,
        "reported_user_id": report_data.reported_user_id,
        "content_type": report_data.content_type,
        "content_id": report_data.content_id,
        "reason": report_data.reason,
        "details": report_data.details,
        "status": "pending",
        "created_at": datetime.utcnow()
    }
    
    result = await db.reports.insert_one(report_doc)
    report_id = str(result.inserted_id)
    
    await db.users.update_one(
        {"_id": ObjectId(report_data.reported_user_id)},
        {"$inc": {"report_count": 1}}
    )
    
    report_count = await db.reports.count_documents({
        "reported_user_id": report_data.reported_user_id,
        "status": "pending"
    })
    
    is_flagged = report_count >= 3
    if is_flagged:
        await db.users.update_one(
            {"_id": ObjectId(report_data.reported_user_id)},
            {"$set": {"flagged": True, "flagged_at": datetime.utcnow()}}
        )
    
    reporter = await db.users.find_one({"_id": current_user["_id"]})
    reported_user = await db.users.find_one({"_id": ObjectId(report_data.reported_user_id)})
    
    priority = "high" if report_count >= 5 else "medium" if report_count >= 3 else "normal"
    
    notification = {
        "type": "new_report",
        "report_id": report_id,
        "reporter": {
            "id": current_user_id,
            "name": reporter.get("full_name") if reporter else "Unknown"
        },
        "reported_user": {
            "id": report_data.reported_user_id,
            "name": reported_user.get("full_name") if reported_user else "Unknown",
            "email": reported_user.get("email") if reported_user else None
        },
        "content_type": report_data.content_type,
        "reason": report_data.reason,
        "details": report_data.details,
        "report_count": report_count,
        "priority": priority,
        "is_flagged": is_flagged,
        "created_at": datetime.utcnow().isoformat()
    }
    
    asyncio.create_task(admin_manager.broadcast_to_admins(notification))
    
    return {"message": "Report submitted successfully", "report_id": report_id}

@router.post("/report/{user_id}")
async def report_user(user_id: str, report_data: dict, current_user: dict = Depends(get_current_user)):
    """Legacy endpoint for backwards compatibility"""
    current_user_id = str(current_user["_id"])
    
    if current_user_id == user_id:
        raise HTTPException(status_code=400, detail="Cannot report yourself")
    
    report_doc = {
        "reporter_id": current_user_id,
        "reported_user_id": user_id,
        "content_type": "profile",
        "content_id": None,
        "reason": report_data.get("reason", "other"),
        "details": report_data.get("notes"),
        "status": "pending",
        "created_at": datetime.utcnow()
    }
    
    await db.reports.insert_one(report_doc)
    
    return {"message": "Report submitted successfully"}

# ==================== ADMIN MODERATION ENDPOINTS ====================

async def get_grouped_moderation_queue_data():
    """Get moderation queue grouped by user with priority sorting"""
    reports = await db.reports.find({"status": "pending"}).to_list(500)
    
    user_reports: Dict[str, list] = {}
    for report in reports:
        user_id = report["reported_user_id"]
        if user_id not in user_reports:
            user_reports[user_id] = []
        user_reports[user_id].append(report)
    
    result = []
    for user_id, user_report_list in user_reports.items():
        reported_user = await db.users.find_one({"_id": ObjectId(user_id)})
        
        report_count = len(user_report_list)
        priority = "critical" if report_count >= 10 else "high" if report_count >= 5 else "medium" if report_count >= 3 else "normal"
        
        reasons = list(set(r.get("reason") for r in user_report_list))
        latest_report = max(user_report_list, key=lambda x: x.get("created_at", datetime.min))
        
        report_details = []
        for r in sorted(user_report_list, key=lambda x: x.get("created_at", datetime.min), reverse=True)[:10]:
            reporter = await db.users.find_one({"_id": ObjectId(r["reporter_id"])})
            report_details.append({
                "id": str(r["_id"]),
                "reporter_name": reporter.get("full_name") if reporter else "Unknown",
                "reason": r.get("reason"),
                "details": r.get("details"),
                "content_type": r.get("content_type"),
                "content_id": r.get("content_id"),
                "created_at": r.get("created_at").isoformat() if r.get("created_at") else None
            })
        
        result.append({
            "user_id": user_id,
            "user": {
                "id": user_id,
                "full_name": reported_user.get("full_name") if reported_user else "Unknown",
                "email": reported_user.get("email") if reported_user else None,
                "profile_photo": reported_user.get("profile_photo") if reported_user else None,
                "moderation_status": reported_user.get("moderation_status", "good_standing") if reported_user else None,
                "warnings_count": reported_user.get("warnings_count", 0) if reported_user else 0,
                "flagged": reported_user.get("flagged", False) if reported_user else False
            },
            "report_count": report_count,
            "priority": priority,
            "reasons": reasons,
            "reports": report_details,
            "latest_report_at": latest_report.get("created_at").isoformat() if latest_report.get("created_at") else None
        })
    
    priority_order = {"critical": 0, "high": 1, "medium": 2, "normal": 3}
    result.sort(key=lambda x: (priority_order.get(x["priority"], 4), -x["report_count"]))
    
    return result

@router.get("/admin/moderation/queue")
async def get_moderation_queue(
    status: Optional[str] = "pending",
    grouped: bool = True,
    current_user: dict = Depends(get_current_user)
):
    await check_admin(current_user)
    
    if grouped:
        return await get_grouped_moderation_queue_data()
    
    query = {}
    if status:
        query["status"] = status
    
    reports = await db.reports.find(query).sort("created_at", -1).to_list(100)
    
    result = []
    for report in reports:
        reporter = await db.users.find_one({"_id": ObjectId(report["reporter_id"])})
        reported_user = await db.users.find_one({"_id": ObjectId(report["reported_user_id"])})
        
        report_count = await db.reports.count_documents({
            "reported_user_id": report["reported_user_id"],
            "status": "pending"
        })
        
        result.append({
            "id": str(report["_id"]),
            "reporter": {
                "id": str(reporter["_id"]) if reporter else None,
                "name": reporter.get("full_name") if reporter else "Unknown"
            },
            "reported_user": {
                "id": str(reported_user["_id"]) if reported_user else None,
                "name": reported_user.get("full_name") if reported_user else "Unknown",
                "email": reported_user.get("email") if reported_user else None,
                "moderation_status": reported_user.get("moderation_status", "good_standing") if reported_user else None,
                "warnings_count": reported_user.get("warnings_count", 0) if reported_user else 0
            },
            "content_type": report.get("content_type"),
            "content_id": report.get("content_id"),
            "reason": report.get("reason"),
            "details": report.get("details"),
            "report_count": report_count,
            "status": report.get("status"),
            "created_at": report.get("created_at")
        })
    
    return result

@router.get("/admin/moderation/stats")
async def get_moderation_stats(current_user: dict = Depends(get_current_user)):
    """Get real-time moderation statistics"""
    await check_admin(current_user)
    
    pending_reports = await db.reports.count_documents({"status": "pending"})
    flagged_users = await db.users.count_documents({"flagged": True})
    warned_users = await db.users.count_documents({"moderation_status": "warned"})
    restricted_users = await db.users.count_documents({"moderation_status": "restricted"})
    suspended_users = await db.users.count_documents({"moderation_status": "suspended"})
    banned_users = await db.users.count_documents({"moderation_status": "banned"})
    
    pipeline = [
        {"$match": {"status": "pending"}},
        {"$group": {"_id": "$reason", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}}
    ]
    reason_breakdown = await db.reports.aggregate(pipeline).to_list(20)
    
    high_priority_pipeline = [
        {"$match": {"status": "pending"}},
        {"$group": {"_id": "$reported_user_id", "count": {"$sum": 1}}},
        {"$match": {"count": {"$gte": 5}}}
    ]
    high_priority_count = len(await db.reports.aggregate(high_priority_pipeline).to_list(100))
    
    return {
        "pending_reports": pending_reports,
        "flagged_users": flagged_users,
        "warned_users": warned_users,
        "restricted_users": restricted_users,
        "suspended_users": suspended_users,
        "banned_users": banned_users,
        "high_priority_cases": high_priority_count,
        "reason_breakdown": {r["_id"]: r["count"] for r in reason_breakdown}
    }

@router.get("/admin/moderation/flagged")
async def get_flagged_users(current_user: dict = Depends(get_current_user)):
    await check_admin(current_user)
    
    flagged_users = await db.users.find({
        "$or": [
            {"flagged": True},
            {"moderation_status": {"$in": ["warned", "restricted", "suspended"]}}
        ]
    }).to_list(100)
    
    result = []
    for user in flagged_users:
        pending_reports = await db.reports.count_documents({
            "reported_user_id": str(user["_id"]),
            "status": "pending"
        })
        
        result.append({
            "id": str(user["_id"]),
            "full_name": user.get("full_name"),
            "email": user.get("email"),
            "moderation_status": user.get("moderation_status", "good_standing"),
            "warnings_count": user.get("warnings_count", 0),
            "flagged": user.get("flagged", False),
            "suspended_until": user.get("suspended_until"),
            "pending_reports": pending_reports
        })
    
    return result

@router.post("/admin/moderation/action/{report_id}")
async def take_moderation_action(
    report_id: str,
    action_data: ModerationAction,
    current_user: dict = Depends(get_current_user)
):
    await check_admin(current_user)
    
    if action_data.action not in MODERATION_ACTIONS:
        raise HTTPException(status_code=400, detail="Invalid moderation action")
    
    report = await db.reports.find_one({"_id": ObjectId(report_id)})
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    
    reported_user_id = report["reported_user_id"]
    
    new_status = "actioned" if action_data.action != "dismiss" else "dismissed"
    await db.reports.update_one(
        {"_id": ObjectId(report_id)},
        {
            "$set": {
                "status": new_status,
                "actioned_by": str(current_user["_id"]),
                "actioned_at": datetime.utcnow(),
                "action_taken": action_data.action,
                "action_reason": action_data.reason
            }
        }
    )
    
    user_update = {}
    
    if action_data.action == "dismiss":
        pending_count = await db.reports.count_documents({
            "reported_user_id": reported_user_id,
            "status": "pending"
        })
        if pending_count == 0:
            await db.users.update_one(
                {"_id": ObjectId(reported_user_id)},
                {"$set": {"flagged": False}}
            )
    
    elif action_data.action == "warn":
        user_update = {
            "$inc": {"warnings_count": 1},
            "$set": {
                "last_warning_at": datetime.utcnow(),
                "last_warning_reason": action_data.reason
            }
        }
        user = await db.users.find_one({"_id": ObjectId(reported_user_id)})
        if user and user.get("warnings_count", 0) >= 2:
            user_update["$set"]["moderation_status"] = "restricted"
    
    elif action_data.action == "remove_content":
        if report.get("content_type") == "portfolio":
            await db.portfolio.delete_one({"_id": ObjectId(report.get("content_id"))})
        elif report.get("content_type") == "gallery":
            await db.gallery.delete_one({"_id": ObjectId(report.get("content_id"))})
        user_update = {"$inc": {"content_removed_count": 1}}
    
    elif action_data.action == "restrict":
        user_update = {
            "$set": {
                "moderation_status": "restricted",
                "restricted_at": datetime.utcnow(),
                "restriction_reason": action_data.reason
            }
        }
    
    elif action_data.action == "suspend":
        duration_days = action_data.duration_days or 7
        suspended_until = datetime.utcnow() + timedelta(days=duration_days)
        user_update = {
            "$set": {
                "moderation_status": "suspended",
                "suspended_at": datetime.utcnow(),
                "suspended_until": suspended_until,
                "suspension_reason": action_data.reason
            }
        }
    
    elif action_data.action == "ban":
        user_update = {
            "$set": {
                "moderation_status": "banned",
                "banned_at": datetime.utcnow(),
                "ban_reason": action_data.reason,
                "flagged": False
            }
        }
    
    if user_update:
        await db.users.update_one(
            {"_id": ObjectId(reported_user_id)},
            user_update
        )
    
    await db.moderation_log.insert_one({
        "admin_id": str(current_user["_id"]),
        "report_id": report_id,
        "target_user_id": reported_user_id,
        "action": action_data.action,
        "reason": action_data.reason,
        "created_at": datetime.utcnow()
    })
    
    reported_user = await db.users.find_one({"_id": ObjectId(reported_user_id)})
    action_notification = {
        "type": "action_taken",
        "report_id": report_id,
        "action": action_data.action,
        "reason": action_data.reason,
        "admin_id": str(current_user["_id"]),
        "admin_name": current_user.get("full_name", "Admin"),
        "target_user": {
            "id": reported_user_id,
            "name": reported_user.get("full_name") if reported_user else "Unknown"
        },
        "created_at": datetime.utcnow().isoformat()
    }
    asyncio.create_task(admin_manager.broadcast_to_admins(action_notification))
    
    return {"message": f"Action '{action_data.action}' applied successfully"}

@router.post("/admin/moderation/action/user/{user_id}")
async def take_bulk_moderation_action(
    user_id: str,
    action_data: ModerationAction,
    current_user: dict = Depends(get_current_user)
):
    """Take action on all pending reports for a specific user"""
    await check_admin(current_user)
    
    if action_data.action not in MODERATION_ACTIONS:
        raise HTTPException(status_code=400, detail="Invalid moderation action")
    
    pending_reports = await db.reports.find({
        "reported_user_id": user_id,
        "status": "pending"
    }).to_list(500)
    
    if not pending_reports:
        raise HTTPException(status_code=404, detail="No pending reports found for this user")
    
    new_status = "actioned" if action_data.action != "dismiss" else "dismissed"
    await db.reports.update_many(
        {"reported_user_id": user_id, "status": "pending"},
        {
            "$set": {
                "status": new_status,
                "actioned_by": str(current_user["_id"]),
                "actioned_at": datetime.utcnow(),
                "action_taken": action_data.action,
                "action_reason": action_data.reason
            }
        }
    )
    
    user_update = {}
    
    if action_data.action == "dismiss":
        await db.users.update_one(
            {"_id": ObjectId(user_id)},
            {"$set": {"flagged": False}}
        )
    elif action_data.action == "warn":
        user_update = {
            "$inc": {"warnings_count": 1},
            "$set": {
                "last_warning_at": datetime.utcnow(),
                "last_warning_reason": action_data.reason
            }
        }
        user = await db.users.find_one({"_id": ObjectId(user_id)})
        if user and user.get("warnings_count", 0) >= 2:
            user_update["$set"]["moderation_status"] = "restricted"
    elif action_data.action == "restrict":
        user_update = {
            "$set": {
                "moderation_status": "restricted",
                "restricted_at": datetime.utcnow(),
                "restriction_reason": action_data.reason,
                "flagged": False
            }
        }
    elif action_data.action == "suspend":
        duration_days = action_data.duration_days or 7
        suspended_until = datetime.utcnow() + timedelta(days=duration_days)
        user_update = {
            "$set": {
                "moderation_status": "suspended",
                "suspended_at": datetime.utcnow(),
                "suspended_until": suspended_until,
                "suspension_reason": action_data.reason,
                "flagged": False
            }
        }
    elif action_data.action == "ban":
        user_update = {
            "$set": {
                "moderation_status": "banned",
                "banned_at": datetime.utcnow(),
                "ban_reason": action_data.reason,
                "flagged": False
            }
        }
    
    if user_update:
        await db.users.update_one({"_id": ObjectId(user_id)}, user_update)
    
    await db.moderation_log.insert_one({
        "admin_id": str(current_user["_id"]),
        "target_user_id": user_id,
        "action": action_data.action,
        "reason": action_data.reason,
        "reports_actioned": len(pending_reports),
        "is_bulk": True,
        "created_at": datetime.utcnow()
    })
    
    reported_user = await db.users.find_one({"_id": ObjectId(user_id)})
    bulk_notification = {
        "type": "bulk_action_taken",
        "action": action_data.action,
        "reason": action_data.reason,
        "admin_name": current_user.get("full_name", "Admin"),
        "target_user": {
            "id": user_id,
            "name": reported_user.get("full_name") if reported_user else "Unknown"
        },
        "reports_actioned": len(pending_reports),
        "created_at": datetime.utcnow().isoformat()
    }
    asyncio.create_task(admin_manager.broadcast_to_admins(bulk_notification))
    
    return {
        "message": f"Action '{action_data.action}' applied to {len(pending_reports)} reports",
        "reports_actioned": len(pending_reports)
    }

@router.get("/admin/moderation/user/{user_id}")
async def get_user_moderation_history(
    user_id: str,
    current_user: dict = Depends(get_current_user)
):
    await check_admin(current_user)
    
    user = await db.users.find_one({"_id": ObjectId(user_id)})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    reports = await db.reports.find({"reported_user_id": user_id}).sort("created_at", -1).to_list(50)
    mod_log = await db.moderation_log.find({"target_user_id": user_id}).sort("created_at", -1).to_list(50)
    
    return {
        "user": {
            "id": str(user["_id"]),
            "full_name": user.get("full_name"),
            "email": user.get("email"),
            "moderation_status": user.get("moderation_status", "good_standing"),
            "warnings_count": user.get("warnings_count", 0),
            "flagged": user.get("flagged", False),
            "suspended_until": user.get("suspended_until"),
            "created_at": user.get("created_at")
        },
        "reports": [{
            "id": str(r["_id"]),
            "reason": r.get("reason"),
            "details": r.get("details"),
            "status": r.get("status"),
            "created_at": r.get("created_at")
        } for r in reports],
        "moderation_actions": [{
            "action": m.get("action"),
            "reason": m.get("reason"),
            "created_at": m.get("created_at")
        } for m in mod_log]
    }

@router.post("/admin/moderation/lift/{user_id}")
async def lift_moderation_status(
    user_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Lift restrictions/suspensions from a user"""
    await check_admin(current_user)
    
    user = await db.users.find_one({"_id": ObjectId(user_id)})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    if user.get("moderation_status") == "banned":
        raise HTTPException(status_code=400, detail="Cannot lift ban through this endpoint. Use appeal process.")
    
    await db.users.update_one(
        {"_id": ObjectId(user_id)},
        {
            "$set": {"moderation_status": "good_standing", "flagged": False},
            "$unset": {"suspended_until": "", "restricted_at": ""}
        }
    )
    
    await db.moderation_log.insert_one({
        "admin_id": str(current_user["_id"]),
        "target_user_id": user_id,
        "action": "lift_restrictions",
        "created_at": datetime.utcnow()
    })
    
    return {"message": "Moderation status lifted successfully"}

# ==================== APPEAL SYSTEM ENDPOINTS ====================

@router.post("/appeals")
async def submit_appeal(appeal_data: AppealCreate, current_user: dict = Depends(get_current_user)):
    """Submit an appeal for a moderation action"""
    user_id = str(current_user["_id"])
    
    status = current_user.get("moderation_status", "good_standing")
    if status not in ["suspended", "banned", "restricted", "warned"]:
        raise HTTPException(status_code=400, detail="No moderation action to appeal")
    
    existing_appeal = await db.appeals.find_one({
        "user_id": user_id,
        "status": {"$in": ["pending", "under_review"]}
    })
    
    if existing_appeal:
        raise HTTPException(status_code=400, detail="You already have a pending appeal. Please wait for a decision.")
    
    appeal_doc = {
        "user_id": user_id,
        "user_email": current_user["email"],
        "user_name": current_user.get("full_name"),
        "moderation_status": status,
        "original_reason": current_user.get("ban_reason") or current_user.get("suspension_reason") or current_user.get("last_warning_reason") or "Policy violation",
        "suspended_until": current_user.get("suspended_until"),
        "appeal_reason": appeal_data.reason,
        "additional_details": appeal_data.additional_details,
        "status": "pending",
        "created_at": datetime.utcnow()
    }
    
    result = await db.appeals.insert_one(appeal_doc)
    
    notification = {
        "type": "new_appeal",
        "appeal_id": str(result.inserted_id),
        "user": {
            "id": user_id,
            "name": current_user.get("full_name"),
            "email": current_user["email"]
        },
        "moderation_status": status,
        "created_at": datetime.utcnow().isoformat()
    }
    asyncio.create_task(admin_manager.broadcast_to_admins(notification))
    
    return {
        "message": "Appeal submitted successfully",
        "appeal_id": str(result.inserted_id),
        "status": "pending"
    }

@router.get("/appeals/me")
async def get_my_appeal(current_user: dict = Depends(get_current_user)):
    """Get the current user's appeal status"""
    user_id = str(current_user["_id"])
    
    appeal = await db.appeals.find_one(
        {"user_id": user_id},
        sort=[("created_at", -1)]
    )
    
    if not appeal:
        return {"has_appeal": False}
    
    return {
        "has_appeal": True,
        "appeal": {
            "id": str(appeal["_id"]),
            "status": appeal.get("status"),
            "appeal_reason": appeal.get("appeal_reason"),
            "admin_notes": appeal.get("admin_notes"),
            "decision_at": appeal.get("decision_at").isoformat() if appeal.get("decision_at") else None,
            "created_at": appeal.get("created_at").isoformat() if appeal.get("created_at") else None
        }
    }

@router.get("/admin/appeals")
async def get_appeals_queue(
    status: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """Get all appeals for admin review"""
    await check_admin(current_user)
    
    query = {}
    if status:
        query["status"] = status
    
    appeals = await db.appeals.find(query).sort("created_at", -1).to_list(100)
    
    result = []
    for appeal in appeals:
        user = await db.users.find_one({"_id": ObjectId(appeal["user_id"])})
        
        result.append({
            "id": str(appeal["_id"]),
            "user": {
                "id": appeal["user_id"],
                "name": appeal.get("user_name") or (user.get("full_name") if user else "Unknown"),
                "email": appeal.get("user_email") or (user.get("email") if user else "Unknown"),
            },
            "moderation_status": appeal.get("moderation_status"),
            "original_reason": appeal.get("original_reason"),
            "suspended_until": appeal.get("suspended_until").isoformat() if appeal.get("suspended_until") else None,
            "appeal_reason": appeal.get("appeal_reason"),
            "additional_details": appeal.get("additional_details"),
            "status": appeal.get("status"),
            "admin_notes": appeal.get("admin_notes"),
            "decided_by": appeal.get("decided_by"),
            "decision_at": appeal.get("decision_at").isoformat() if appeal.get("decision_at") else None,
            "created_at": appeal.get("created_at").isoformat() if appeal.get("created_at") else None
        })
    
    return result

@router.get("/admin/appeals/stats")
async def get_appeals_stats(current_user: dict = Depends(get_current_user)):
    """Get appeal statistics"""
    await check_admin(current_user)
    
    pending = await db.appeals.count_documents({"status": "pending"})
    under_review = await db.appeals.count_documents({"status": "under_review"})
    approved = await db.appeals.count_documents({"status": "approved"})
    denied = await db.appeals.count_documents({"status": "denied"})
    
    return {
        "pending": pending,
        "under_review": under_review,
        "approved": approved,
        "denied": denied,
        "total": pending + under_review + approved + denied
    }

@router.post("/admin/appeals/{appeal_id}/action")
async def process_appeal(
    appeal_id: str,
    action_data: AppealAction,
    current_user: dict = Depends(get_current_user)
):
    """Process an appeal (approve or deny)"""
    await check_admin(current_user)
    
    if action_data.action not in ["approve", "deny"]:
        raise HTTPException(status_code=400, detail="Invalid action. Use 'approve' or 'deny'.")
    
    appeal = await db.appeals.find_one({"_id": ObjectId(appeal_id)})
    if not appeal:
        raise HTTPException(status_code=404, detail="Appeal not found")
    
    if appeal.get("status") in ["approved", "denied"]:
        raise HTTPException(status_code=400, detail="This appeal has already been processed")
    
    user_id = appeal["user_id"]
    original_status = appeal.get("moderation_status")
    
    new_status = "approved" if action_data.action == "approve" else "denied"
    await db.appeals.update_one(
        {"_id": ObjectId(appeal_id)},
        {
            "$set": {
                "status": new_status,
                "admin_notes": action_data.admin_notes,
                "decided_by": str(current_user["_id"]),
                "decided_by_name": current_user.get("full_name"),
                "decision_at": datetime.utcnow()
            }
        }
    )
    
    restored_status = None
    if action_data.action == "approve":
        if original_status == "banned":
            restored_status = "warned"
        else:
            restored_status = "good_standing"
        
        await db.users.update_one(
            {"_id": ObjectId(user_id)},
            {
                "$set": {
                    "moderation_status": restored_status,
                    "flagged": False,
                    "appeal_approved_at": datetime.utcnow(),
                    "final_warning": True,
                    "final_warning_at": datetime.utcnow(),
                    "final_warning_reason": f"Restored via appeal from {original_status}. Next violation will escalate faster."
                },
                "$unset": {
                    "suspended_until": "",
                    "suspension_reason": "",
                    "ban_reason": "",
                    "banned_at": "",
                    "suspended_at": "",
                    "restricted_at": "",
                    "restriction_reason": ""
                }
            }
        )
        
        await db.moderation_log.insert_one({
            "admin_id": str(current_user["_id"]),
            "target_user_id": user_id,
            "action": "appeal_approved",
            "appeal_id": appeal_id,
            "original_status": original_status,
            "restored_status": restored_status,
            "final_warning_applied": True,
            "notes": action_data.admin_notes,
            "created_at": datetime.utcnow()
        })
    else:
        await db.moderation_log.insert_one({
            "admin_id": str(current_user["_id"]),
            "target_user_id": user_id,
            "action": "appeal_denied",
            "appeal_id": appeal_id,
            "original_status": original_status,
            "notes": action_data.admin_notes,
            "created_at": datetime.utcnow()
        })
    
    notification = {
        "type": "appeal_processed",
        "appeal_id": appeal_id,
        "action": action_data.action,
        "original_status": original_status,
        "admin_name": current_user.get("full_name"),
        "created_at": datetime.utcnow().isoformat()
    }
    asyncio.create_task(admin_manager.broadcast_to_admins(notification))
    
    return {
        "message": f"Appeal {action_data.action}d successfully",
        "appeal_status": new_status,
        "restored_status": restored_status if action_data.action == "approve" else None,
        "final_warning_applied": action_data.action == "approve"
    }

@router.patch("/admin/appeals/{appeal_id}/review")
async def mark_appeal_under_review(
    appeal_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Mark an appeal as under review"""
    await check_admin(current_user)
    
    appeal = await db.appeals.find_one({"_id": ObjectId(appeal_id)})
    if not appeal:
        raise HTTPException(status_code=404, detail="Appeal not found")
    
    if appeal.get("status") != "pending":
        raise HTTPException(status_code=400, detail="Only pending appeals can be marked as under review")
    
    await db.appeals.update_one(
        {"_id": ObjectId(appeal_id)},
        {
            "$set": {
                "status": "under_review",
                "reviewed_by": str(current_user["_id"]),
                "review_started_at": datetime.utcnow()
            }
        }
    )
    
    return {"message": "Appeal marked as under review"}

# ==================== USER MODERATION STATUS CHECK ====================

@router.get("/moderation/status")
async def get_moderation_status(current_user: dict = Depends(get_current_user)):
    """Get current user's moderation status"""
    return {
        "status": current_user.get("moderation_status", "good_standing"),
        "warnings_count": current_user.get("warnings_count", 0),
        "last_warning_reason": current_user.get("last_warning_reason"),
        "suspended_until": current_user.get("suspended_until").isoformat() if current_user.get("suspended_until") else None,
        "suspension_reason": current_user.get("suspension_reason"),
        "ban_reason": current_user.get("ban_reason"),
    }


# ==================== GUARDIAN DASHBOARD - SYSTEM ACTIONS LOG ====================

@router.get("/admin/guardian/actions")
async def get_system_actions(
    limit: int = 50,
    action_type: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """
    Guardian Dashboard: Get history of system-automated actions.
    This shows RESULTS, not pending items requiring action.
    """
    await check_admin(current_user)
    
    query = {}
    if action_type:
        query["type"] = action_type
    
    actions = await db.system_actions.find(query).sort("created_at", -1).limit(limit).to_list(limit)
    
    result = []
    for action in actions:
        result.append({
            "id": str(action["_id"]),
            "type": action.get("type"),
            "user_id": action.get("user_id"),
            "user_name": action.get("user_name"),
            "user_email": action.get("user_email"),
            "strike_number": action.get("strike_number"),
            "action": action.get("action"),
            "action_label": action.get("action_label"),
            "violation_type": action.get("violation_type"),
            "duration_hours": action.get("duration_hours"),
            "suspended_until": action.get("suspended_until").isoformat() if action.get("suspended_until") else None,
            "message": action.get("message"),
            "created_at": action.get("created_at").isoformat() if action.get("created_at") else None,
            "requires_admin_action": action.get("requires_admin_action", False),
            "status": action.get("status", "completed")
        })
    
    return result

@router.get("/admin/guardian/summary")
async def get_guardian_summary(current_user: dict = Depends(get_current_user)):
    """
    Guardian Dashboard: Summary of system health and recent actions.
    Shows what the system HAS DONE, not what needs to be done.
    """
    await check_admin(current_user)
    
    now = datetime.utcnow()
    last_24h = now - timedelta(hours=24)
    last_7d = now - timedelta(days=7)
    
    # Actions in last 24 hours
    actions_24h = await db.system_actions.count_documents({
        "created_at": {"$gte": last_24h}
    })
    
    # Actions in last 7 days
    actions_7d = await db.system_actions.count_documents({
        "created_at": {"$gte": last_7d}
    })
    
    # Currently suspended users (will auto-restore)
    currently_suspended = await db.users.count_documents({
        "moderation_status": "suspended",
        "suspended_until": {"$gt": now}
    })
    
    # Users restored in last 24h
    restored_24h = await db.system_actions.count_documents({
        "type": "system_auto_restore",
        "created_at": {"$gte": last_24h}
    })
    
    # Banned users (require appeal)
    banned_users = await db.users.count_documents({
        "moderation_status": "banned"
    })
    
    # Pending appeals (only thing requiring attention)
    pending_appeals = await db.appeals.count_documents({
        "status": "pending"
    })
    
    # Get last 5 system actions for quick view
    recent_actions = await db.system_actions.find().sort("created_at", -1).limit(5).to_list(5)
    
    return {
        "system_health": "operational",
        "actions_last_24h": actions_24h,
        "actions_last_7d": actions_7d,
        "currently_suspended": currently_suspended,
        "restored_last_24h": restored_24h,
        "banned_users": banned_users,
        "pending_appeals": pending_appeals,
        "requires_attention": pending_appeals > 0,
        "recent_actions": [{
            "type": a.get("type"),
            "user_name": a.get("user_name"),
            "action_label": a.get("action_label"),
            "message": a.get("message"),
            "created_at": a.get("created_at").isoformat() if a.get("created_at") else None
        } for a in recent_actions]
    }

@router.get("/admin/guardian/active-suspensions")
async def get_active_suspensions(current_user: dict = Depends(get_current_user)):
    """
    Guardian Dashboard: List of currently active suspensions with countdown timers.
    These will auto-restore - no action needed.
    """
    await check_admin(current_user)
    
    now = datetime.utcnow()
    
    suspended_users = await db.users.find({
        "moderation_status": "suspended",
        "suspended_until": {"$gt": now}
    }).to_list(100)
    
    result = []
    for user in suspended_users:
        suspended_until = user.get("suspended_until")
        time_remaining = suspended_until - now if suspended_until else timedelta(0)
        
        result.append({
            "user_id": str(user["_id"]),
            "user_name": user.get("full_name"),
            "user_email": user.get("email"),
            "strike_count": user.get("strike_count", 0),
            "suspension_reason": user.get("suspension_reason"),
            "suspended_at": user.get("suspended_at").isoformat() if user.get("suspended_at") else None,
            "suspended_until": suspended_until.isoformat() if suspended_until else None,
            "hours_remaining": round(time_remaining.total_seconds() / 3600, 1),
            "auto_restore": True,
            "status": "WILL_AUTO_RESTORE"
        })
    
    return {
        "count": len(result),
        "note": "All suspensions will automatically expire. No action required.",
        "suspensions": result
    }



# Export admin_manager for WebSocket use in main app
def get_admin_manager():
    return admin_manager

def get_grouped_queue_func():
    return get_grouped_moderation_queue_data
