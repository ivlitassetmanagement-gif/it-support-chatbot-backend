"""Updated chat routes with follow-up questions"""
from fastapi import APIRouter, UploadFile, File, HTTPException, Request
from pydantic import BaseModel
from typing import Optional, List
from app.services.rag_service import RAGService
from app.services.llm_service import LLMService
from app.services.conversation_service import ConversationService
from app.services.database_service import DatabaseService
from app.services.follow_up_service import FollowUpQuestionService
import logging
import uuid

logger = logging.getLogger(__name__)

router = APIRouter()
rag = RAGService()
llm = LLMService()
conversation_service = ConversationService()
db_service = DatabaseService()
follow_up_service = FollowUpQuestionService()


class ChatAskRequest(BaseModel):
    message: str
    conversation_id: Optional[str] = None

    class Config:
        extra = "ignore"


@router.post('/chat/message')
async def chat_message(request_data: ChatAskRequest, request: Request):
    """Send chat message with RAG and follow-up questions"""
    try:
        user_id = request.state.user_id if hasattr(request.state, 'user_id') else 'unknown'
        conversation_id = request_data.conversation_id or str(uuid.uuid4())
        message = request_data.message.strip()

        if not message:
            raise HTTPException(status_code=400, detail="Message cannot be empty")

        logger.info(f"Chat from user {user_id}: {message[:50]}")

        # Save user message
        conversation_service.save_message(
            conversation_id=conversation_id,
            role="user",
            content=message,
            metadata={"user_id": user_id}
        )

        db_service.save_message(
            conversation_id=conversation_id,
            role="user",
            content=message,
            user_id=user_id,
            metadata={"user_id": user_id}
        )

        # Retrieve relevant documents using RAG
        try:
            docs_text, sources = rag.retrieve(message, top_k=4)
        except Exception as rag_error:
            logger.warning(f"RAG retrieval failed: {rag_error}")
            docs_text = ""
            sources = []

        # Generate AI response
        try:
            answer = llm.generate_response(message, docs_text)
        except Exception as llm_error:
            logger.error(f"LLM generation failed: {llm_error}")
            answer = f"I apologize, but I encountered an error processing your request. Please try again."
            sources = []

        source_type = "document" if sources and docs_text else "web"
        confidence = "high" if sources and docs_text else "medium"

        # Generate follow-up questions
        try:
            follow_up_questions = follow_up_service.generate_follow_up_questions(
                user_message=message,
                assistant_response=answer,
                num_questions=3
            )
        except Exception as e:
            logger.warning(f"Follow-up question generation failed: {e}")
            follow_up_questions = []

        # Save bot response with metadata
        conversation_service.save_message(
            conversation_id=conversation_id,
            role="bot",
            content=answer,
            metadata={
                "source_type": source_type,
                "confidence": confidence,
                "sources": sources or [],
                "follow_up_questions": follow_up_questions
            }
        )

        db_service.save_message(
            conversation_id=conversation_id,
            role="bot",
            content=answer,
            user_id=user_id,
            metadata={
                "source_type": source_type,
                "confidence": confidence,
                "sources": sources or [],
                "follow_up_questions": follow_up_questions
            }
        )

        return {
            "conversation_id": conversation_id,
            "answer": answer,
            "sources": sources or [],
            "source_type": source_type,
            "confidence": confidence,
            "follow_up_questions": follow_up_questions
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in chat: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Chat error: {str(e)[:100]}")


@router.get('/chat/history/{conversation_id}')
async def get_conversation_history(conversation_id: str, request: Request):
    """Retrieve conversation history with follow-up questions"""
    try:
        user_id = request.state.user_id if hasattr(request.state, 'user_id') else 'unknown'

        # Try database first
        conversation = None
        if db_service.is_connected:
            conversation = db_service.get_conversation(conversation_id)

        # Fallback to files
        if not conversation:
            conversation = conversation_service.get_conversation(conversation_id)

        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation not found")

        logger.info(f"Retrieved conversation: {conversation_id}")
        return conversation

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving history: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get('/chat/conversations')
async def list_conversations(request: Request, limit: int = 50, user_only: bool = False):
    """List conversations (optionally filtered by user)"""
    try:
        user_id = request.state.user_id if hasattr(request.state, 'user_id') else 'unknown'

        conversations = []
        if db_service.is_connected:
            if user_only and user_id != 'unknown':
                conversations = db_service.get_user_conversations(user_id=user_id, limit=limit)
            else:
                conversations = db_service.list_conversations(user_id=None, limit=limit)

        if not conversations:
            conversations = conversation_service.list_conversations(limit=limit)

        logger.info(f"Listed {len(conversations)} conversations for user {user_id}")

        return {
            "total": len(conversations),
            "user_id": user_id,
            "conversations": conversations
        }
    except Exception as e:
        logger.error(f"Error listing conversations: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete('/chat/{conversation_id}')
async def delete_conversation(conversation_id: str, request: Request):
    """Delete a conversation"""
    try:
        user_id = request.state.user_id if hasattr(request.state, 'user_id') else 'unknown'

        if db_service.is_connected:
            success = db_service.delete_conversation(conversation_id)
            if success:
                logger.info(f"Deleted conversation: {conversation_id}")
                return {"status": "success", "message": "Conversation deleted"}

        raise HTTPException(status_code=404, detail="Conversation not found")

    except Exception as e:
        logger.error(f"Error deleting conversation: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post('/chat/search')
async def search_conversations(request: Request, limit: int = 10):
    """Search through conversations by message content"""
    try:
        user_id = request.state.user_id if hasattr(request.state, 'user_id') else 'unknown'

        body = await request.json()
        query = body.get('query', '').strip()

        if not query:
            raise HTTPException(status_code=400, detail="Query parameter required")

        # Search in database if connected
        if db_service.is_connected:
            results = db_service.search_messages(query, limit=limit)

            return {
                "query": query,
                "results": results,
                "count": len(results),
                "user_id": user_id
            }

        raise HTTPException(status_code=503, detail="Search not available")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error searching conversations: {e}")
        raise HTTPException(status_code=500, detail=str(e))
