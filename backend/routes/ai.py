from fastapi import APIRouter, Depends, HTTPException
from datetime import datetime
import logging
from emergentintegrations.llm.chat import LlmChat, UserMessage

from core.database import db
from core.config import settings
from core.dependencies import get_current_user
from models.ai import AIMessageRequest, AIMessageResponse

router = APIRouter(prefix="/ai", tags=["AI"])

@router.post("/chat", response_model=AIMessageResponse)
async def ai_chat(request: AIMessageRequest, current_user: dict = Depends(get_current_user)):
    try:
        # Get user context
        user_id = str(current_user["_id"])
        clients_count = await db.clients.count_documents({"user_id": user_id})
        appointments_count = await db.appointments.count_documents({"user_id": user_id})
        
        # Create system message with context
        system_message = f"""You are StyleFlow AI, an intelligent assistant for hairstylists. You help with:
- Client follow-up suggestions and rebooking reminders
- Formula recall and hair color recommendations
- Business insights and revenue tracking
- Content ideas for social media
- Product upsell suggestions based on client history
- Retention strategies

Current user context:
- Total clients: {clients_count}
- Total appointments: {appointments_count}

Be helpful, professional, and focused on helping the stylist grow their business."""

        # Additional context if provided
        if request.context:
            system_message += f"\n\nAdditional context: {request.context}"
        
        # Initialize LLM Chat
        chat = LlmChat(
            api_key=settings.EMERGENT_LLM_KEY,
            session_id=f"styleflow_{user_id}_{datetime.utcnow().timestamp()}",
            system_message=system_message
        ).with_model("openai", "gpt-4o")
        
        # Send message
        user_message = UserMessage(text=request.message)
        response = await chat.send_message(user_message)
        
        return AIMessageResponse(response=response)
    
    except Exception as e:
        logging.error(f"AI chat error: {str(e)}")
        raise HTTPException(status_code=500, detail="AI assistant unavailable")
