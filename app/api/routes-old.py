from fastapi import APIRouter, UploadFile, File, HTTPException, Request
from pydantic import BaseModel
from typing import Optional, List
from app.services.rag_service import RAGService
from app.services.llm_service import LLMService
from app.services.conversation_service import ConversationService
from app.services.database_service import DatabaseService
import logging
import uuid

logger = logging.getLogger(__name__)

router = APIRouter()
rag = RAGService()
llm = LLMService()
conversation_service = ConversationService()
db_service = DatabaseService()

class ChatRequest(BaseModel):
    question: str

class ChatAskRequest(BaseModel):
    message: str
    conversation_id: Optional[str] = None

    class Config:
        extra = "ignore"

@router.get('/health')
async def health():
    '''Health check (no auth required)'''
    return {"status": "ok", "version": "2.0-chromadb"}

@router.get('/health/db')
async def health_db():
    '''Database health check'''
    db_connected = db_service.is_connected and db_service.test_connection()

    return {
        "status": "ok" if db_connected else "warning",
        "database": "connected" if db_connected else "not connected",
        "conversation_storage": "database" if db_connected else "file-based"
    }

@router.post('/upload-kb')
async def upload_kb(file: UploadFile = File(...), request: Request = None):
    '''Upload and index document with ChromaDB'''
    try:
        user_id = request.state.user_id if hasattr(request.state, 'user_id') else 'unknown'
        
        file_path = f"./storage/docs/{file.filename}"
        with open(file_path, "wb") as f:
            content = await file.read()
            f.write(content)
        
        result = rag.index_file(file_path)
        logger.info(f"User {user_id} uploaded: {file.filename}")
        
        return {**result, "uploaded_by": user_id}
    except Exception as e:
        logger.error(f"Error uploading file: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post('/chat')
async def chat(request_data: ChatRequest, request: Request):
    '''Chat with semantic search using ChromaDB'''
    try:
        user_id = request.state.user_id if hasattr(request.state, 'user_id') else 'unknown'
        logger.info(f"Chat query from user {user_id}: {request_data.question[:50]}")

        docs_text, sources = rag.retrieve(request_data.question, top_k=4)
        answer = llm.generate_response(request_data.question, docs_text)
        confidence = "high" if sources else "low"

        return {
            "answer": answer,
            "sources": sources,
            "confidence": confidence,
            "user_id": user_id
        }
    except Exception as e:
        logger.error(f"Error processing chat: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post('/chat/ask')
async def chat_ask(request_data: ChatAskRequest, request: Request):
    '''Chat endpoint compatible with web frontend - Auto-saves history'''
    try:
        user_id = request.state.user_id if hasattr(request.state, 'user_id') else 'unknown'
        conversation_id = request_data.conversation_id or str(uuid.uuid4())
        message = request_data.message.strip()

        if not message:
            raise HTTPException(status_code=400, detail="Message cannot be empty")

        logger.info(f"Chat from user {user_id}: {message[:50]}")

        # Save user message to history (both file and database)
        conversation_service.save_message(
            conversation_id=conversation_id,
            role="user",
            content=message,
            metadata={"user_id": user_id}
        )

        # Also save to database if connected
        db_service.save_message(
            conversation_id=conversation_id,
            role="user",
            content=message,
            user_id=user_id,
            metadata={"user_id": user_id}
        )

        try:
            docs_text, sources = rag.retrieve(message, top_k=4)
        except Exception as rag_error:
            logger.warning(f"RAG retrieval failed: {rag_error}, continuing without documents")
            docs_text = ""
            sources = []

        try:
            answer = llm.generate_response(message, docs_text)
        except Exception as llm_error:
            logger.error(f"LLM generation failed: {llm_error}")
            answer = f"I encountered an error processing your request: {str(llm_error)[:100]}"

        source_type = "document" if sources and docs_text else "web"
        confidence = "high" if sources and docs_text else "medium"

        # Save bot response to history (both file and database)
        conversation_service.save_message(
            conversation_id=conversation_id,
            role="bot",
            content=answer,
            metadata={
                "source_type": source_type,
                "confidence": confidence,
                "sources": sources or []
            }
        )

        # Also save to database if connected
        db_service.save_message(
            conversation_id=conversation_id,
            role="bot",
            content=answer,
            user_id=user_id,
            metadata={
                "source_type": source_type,
                "confidence": confidence,
                "sources": sources or []
            }
        )

        return {
            "conversation_id": conversation_id,
            "answer": answer,
            "sources": sources or [],
            "source_type": source_type,
            "confidence": confidence
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in chat/ask: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Chat error: {str(e)[:100]}")

@router.get('/chat/history/{conversation_id}')
async def get_conversation_history(conversation_id: str, request: Request):
    '''Retrieve conversation history - From database with fallback to files'''
    try:
        user_id = request.state.user_id if hasattr(request.state, 'user_id') else 'unknown'

        # Try database first (if connected)
        conversation = None
        if db_service.is_connected:
            conversation = db_service.get_conversation(conversation_id)

        # Fallback to file-based history if database unavailable
        if not conversation:
            conversation = conversation_service.get_conversation(conversation_id)

        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation not found")

        logger.info(f"Retrieved conversation history for {conversation_id}")

        return conversation

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving history: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get('/chat/conversations')
async def list_conversations(request: Request, limit: int = 50):
    '''List all saved conversations - From database with fallback to files'''
    try:
        user_id = request.state.user_id if hasattr(request.state, 'user_id') else 'unknown'

        # Try database first (if connected)
        conversations = []
        if db_service.is_connected:
            conversations = db_service.list_conversations(user_id=None, limit=limit)

        # Fallback to file-based if database unavailable
        if not conversations:
            conversations = conversation_service.list_conversations(limit=limit)

        logger.info(f"Listed {len(conversations)} conversations for user {user_id}")

        return {
            "total": len(conversations),
            "conversations": conversations
        }
    except Exception as e:
        logger.error(f"Error listing conversations: {e}")
        raise HTTPException(status_code=500, detail=str(e))
