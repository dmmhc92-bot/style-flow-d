"""
StyleFlow Automated Strike & Recovery Engine
============================================
Self-governing moderation system that handles violations automatically.
No manual admin intervention required for standard violations.
"""

from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from bson import ObjectId
import logging

logger = logging.getLogger(__name__)

# ==================== STRIKE TABLE ====================

STRIKE_TABLE = {
    1: {"action": "warning", "duration_hours": 0, "label": "Warning"},
    2: {"action": "suspend", "duration_hours": 24, "label": "24-Hour Lock"},
    3: {"action": "suspend", "duration_hours": 72, "label": "72-Hour Lock"},
    4: {"action": "suspend", "duration_hours": 168, "label": "7-Day Lock"},
    5: {"action": "suspend", "duration_hours": 720, "label": "30-Day Suspension"},
    6: {"action": "ban", "duration_hours": None, "label": "Permanent Ban"},
}

# Severity escalation - certain violations skip strike levels
SEVERITY_ESCALATION = {
    "harassment": 2,       # Skip to Strike 2
    "hate_speech": 3,      # Skip to Strike 3
    "sexual_content": 3,   # Skip to Strike 3
    "illegal": 6,          # Instant permanent ban
    "impersonation": 2,    # Skip to Strike 2
    "spam": 1,             # Normal progression
    "inappropriate": 1,    # Normal progression
    "other": 1,            # Normal progression
}

# Report thresholds for auto-action
AUTO_ACTION_THRESHOLDS = {
    "warning_threshold": 3,      # 3 reports = automatic warning
    "escalation_threshold": 3,   # 3 more reports after warning = next strike
}

# Recovery settings
STRIKE_DECAY_DAYS = 90           # Strikes decay after 90 days clean
CLEAN_SLATE_DAYS = 180           # Full reset after 180 days clean


class StrikeEngine:
    """Autonomous moderation engine that handles violations without manual intervention."""
    
    def __init__(self, db):
        self.db = db
    
    async def process_violation(
        self, 
        user_id: str, 
        violation_type: str,
        report_ids: list = None,
        details: str = None
    ) -> Dict[str, Any]:
        """
        Process a violation and automatically apply the appropriate strike.
        Returns the action taken for notification purposes.
        """
        user = await self.db.users.find_one({"_id": ObjectId(user_id)})
        if not user:
            return {"error": "User not found"}
        
        # Get current strike count
        current_strikes = user.get("strike_count", 0)
        
        # Check for strike decay
        current_strikes = await self._apply_strike_decay(user_id, user, current_strikes)
        
        # Determine new strike level based on severity
        severity_level = SEVERITY_ESCALATION.get(violation_type, 1)
        new_strike = max(current_strikes + 1, severity_level)
        
        # Cap at 6 (permanent ban)
        new_strike = min(new_strike, 6)
        
        # Get the action for this strike level
        strike_config = STRIKE_TABLE.get(new_strike, STRIKE_TABLE[6])
        
        # Apply the action
        action_result = await self._apply_strike_action(
            user_id=user_id,
            user=user,
            new_strike=new_strike,
            strike_config=strike_config,
            violation_type=violation_type,
            report_ids=report_ids,
            details=details
        )
        
        return action_result
    
    async def _apply_strike_decay(
        self, 
        user_id: str, 
        user: dict, 
        current_strikes: int
    ) -> int:
        """Apply strike decay for users who have been clean."""
        last_violation = user.get("last_violation_at")
        
        if not last_violation or current_strikes == 0:
            return current_strikes
        
        days_clean = (datetime.utcnow() - last_violation).days
        
        # Clean slate after 180 days
        if days_clean >= CLEAN_SLATE_DAYS:
            await self.db.users.update_one(
                {"_id": ObjectId(user_id)},
                {"$set": {"strike_count": 0, "strikes_decayed_at": datetime.utcnow()}}
            )
            return 0
        
        # Decay by 1 strike per 90 days
        decay_amount = days_clean // STRIKE_DECAY_DAYS
        if decay_amount > 0:
            new_strikes = max(0, current_strikes - decay_amount)
            await self.db.users.update_one(
                {"_id": ObjectId(user_id)},
                {"$set": {"strike_count": new_strikes, "strikes_decayed_at": datetime.utcnow()}}
            )
            return new_strikes
        
        return current_strikes
    
    async def _apply_strike_action(
        self,
        user_id: str,
        user: dict,
        new_strike: int,
        strike_config: dict,
        violation_type: str,
        report_ids: list = None,
        details: str = None
    ) -> Dict[str, Any]:
        """Apply the strike action to the user."""
        
        action = strike_config["action"]
        duration_hours = strike_config["duration_hours"]
        label = strike_config["label"]
        
        update_data = {
            "strike_count": new_strike,
            "last_violation_at": datetime.utcnow(),
            "last_violation_type": violation_type,
        }
        
        suspended_until = None
        
        if action == "warning":
            update_data["moderation_status"] = "warned"
            update_data["warnings_count"] = user.get("warnings_count", 0) + 1
            update_data["last_warning_at"] = datetime.utcnow()
            update_data["last_warning_reason"] = f"Strike {new_strike}: {violation_type}"
            
        elif action == "suspend":
            suspended_until = datetime.utcnow() + timedelta(hours=duration_hours)
            update_data["moderation_status"] = "suspended"
            update_data["suspended_at"] = datetime.utcnow()
            update_data["suspended_until"] = suspended_until
            update_data["suspension_reason"] = f"Strike {new_strike}: {violation_type}"
            update_data["auto_restore_scheduled"] = True
            
        elif action == "ban":
            update_data["moderation_status"] = "banned"
            update_data["banned_at"] = datetime.utcnow()
            update_data["ban_reason"] = f"Strike {new_strike}: {violation_type} - Permanent ban"
        
        # Mark as final warning if strike 4+
        if new_strike >= 4:
            update_data["final_warning"] = True
            update_data["final_warning_at"] = datetime.utcnow()
        
        # Update user
        await self.db.users.update_one(
            {"_id": ObjectId(user_id)},
            {"$set": update_data}
        )
        
        # Mark reports as auto-actioned
        if report_ids:
            await self.db.reports.update_many(
                {"_id": {"$in": [ObjectId(rid) for rid in report_ids]}},
                {
                    "$set": {
                        "status": "auto_actioned",
                        "auto_action": action,
                        "auto_actioned_at": datetime.utcnow()
                    }
                }
            )
        
        # Create system action log
        action_log = {
            "type": "system_auto_action",
            "user_id": user_id,
            "user_name": user.get("full_name", "Unknown"),
            "user_email": user.get("email", "Unknown"),
            "strike_number": new_strike,
            "action": action,
            "action_label": label,
            "violation_type": violation_type,
            "duration_hours": duration_hours,
            "suspended_until": suspended_until,
            "details": details,
            "report_ids": report_ids or [],
            "created_at": datetime.utcnow(),
            "requires_admin_action": False,
            "status": "completed"
        }
        
        await self.db.system_actions.insert_one(action_log)
        
        # Update user flagged status
        if action in ["suspend", "ban"]:
            await self.db.users.update_one(
                {"_id": ObjectId(user_id)},
                {"$set": {"flagged": True, "flagged_at": datetime.utcnow()}}
            )
        
        logger.info(f"STRIKE ENGINE: Applied {label} to user {user_id} for {violation_type}")
        
        return {
            "success": True,
            "user_id": user_id,
            "user_name": user.get("full_name"),
            "strike_number": new_strike,
            "action": action,
            "action_label": label,
            "violation_type": violation_type,
            "duration_hours": duration_hours,
            "suspended_until": suspended_until.isoformat() if suspended_until else None,
            "message": f"System automatically applied {label} for {violation_type}"
        }
    
    async def check_and_restore_expired_suspensions(self) -> list:
        """
        Check for expired suspensions and automatically restore users.
        Called periodically by background task.
        """
        now = datetime.utcnow()
        
        # Find users with expired suspensions
        expired_users = await self.db.users.find({
            "moderation_status": "suspended",
            "suspended_until": {"$lte": now},
            "auto_restore_scheduled": True
        }).to_list(100)
        
        restored = []
        
        for user in expired_users:
            user_id = str(user["_id"])
            strike_count = user.get("strike_count", 0)
            
            # Determine restoration status
            if strike_count >= 4:
                new_status = "warned"  # Stay on probation
            else:
                new_status = "good_standing"
            
            # Restore user
            await self.db.users.update_one(
                {"_id": user["_id"]},
                {
                    "$set": {
                        "moderation_status": new_status,
                        "flagged": False,
                        "restored_at": now,
                        "auto_restore_scheduled": False
                    },
                    "$unset": {
                        "suspended_until": "",
                        "suspension_reason": ""
                    }
                }
            )
            
            # Log restoration
            restoration_log = {
                "type": "system_auto_restore",
                "user_id": user_id,
                "user_name": user.get("full_name", "Unknown"),
                "user_email": user.get("email", "Unknown"),
                "previous_status": "suspended",
                "new_status": new_status,
                "strike_count": strike_count,
                "restored_at": now,
                "message": f"User automatically restored to {new_status} after suspension expired"
            }
            
            await self.db.system_actions.insert_one(restoration_log)
            
            restored.append({
                "user_id": user_id,
                "user_name": user.get("full_name"),
                "new_status": new_status
            })
            
            logger.info(f"STRIKE ENGINE: Auto-restored user {user_id} to {new_status}")
        
        return restored
    
    async def check_report_thresholds(self) -> list:
        """
        Check for users who have reached report thresholds and auto-action.
        Called periodically by background task.
        """
        actions_taken = []
        
        # Aggregate pending reports by user
        pipeline = [
            {"$match": {"status": "pending"}},
            {"$group": {
                "_id": "$reported_user_id",
                "count": {"$sum": 1},
                "reasons": {"$push": "$reason"},
                "report_ids": {"$push": {"$toString": "$_id"}}
            }},
            {"$match": {"count": {"$gte": AUTO_ACTION_THRESHOLDS["warning_threshold"]}}}
        ]
        
        threshold_users = await self.db.reports.aggregate(pipeline).to_list(100)
        
        for user_data in threshold_users:
            user_id = user_data["_id"]
            report_count = user_data["count"]
            reasons = user_data["reasons"]
            report_ids = user_data["report_ids"]
            
            # Get the most severe violation type
            severity_order = ["illegal", "hate_speech", "sexual_content", "harassment", "impersonation", "spam", "inappropriate", "other"]
            most_severe = "other"
            for severity in severity_order:
                if severity in reasons:
                    most_severe = severity
                    break
            
            # Process the violation
            result = await self.process_violation(
                user_id=user_id,
                violation_type=most_severe,
                report_ids=report_ids,
                details=f"Auto-triggered: {report_count} reports received"
            )
            
            if result.get("success"):
                actions_taken.append(result)
        
        return actions_taken


# Background task runner
async def run_strike_engine_tasks(db):
    """Run periodic strike engine tasks."""
    engine = StrikeEngine(db)
    
    # Check and restore expired suspensions
    restored = await engine.check_and_restore_expired_suspensions()
    
    # Check report thresholds and auto-action
    actions = await engine.check_report_thresholds()
    
    return {
        "restored_users": restored,
        "auto_actions": actions,
        "timestamp": datetime.utcnow().isoformat()
    }
