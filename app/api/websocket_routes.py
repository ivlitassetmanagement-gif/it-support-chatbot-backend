from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException
from typing import List, Dict
import json
import logging
from datetime import datetime
from app.services.llm_service import LLMService
from app.services.rag_service import RAGService
from app.services.database_service import DatabaseService
import uuid

logger = logging.getLogger(__name__)
router = APIRouter()

class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, List[WebSocket]] = {}
        self.user_typing: Dict[str, bool] = {}
        self.rag = RAGService()
        self.llm = LLMService()
        self.db = DatabaseService()

    async def connect(self, websocket: WebSocket, conversation_id: str):
        await websocket.accept()
        if conversation_id not in self.active_connections:
            self.active_connections[conversation_id] = []
        self.active_connections[conversation_id].append(websocket)
        logger.info(f"Client connected to conversation {conversation_id}")

    def disconnect(self, conversation_id: str, websocket: WebSocket):
        if conversation_id in self.active_connections:
            self.active_connections[conversation_id].remove(websocket)
            if not self.active_connections[conversation_id]:
                del self.active_connections[conversation_id]
        logger.info(f"Client disconnected from conversation {conversation_id}")

    async def broadcast(self, conversation_id: str, message: dict):
        if conversation_id in self.active_connections:
            for connection in self.active_connections[conversation_id]:
                try:
                    await connection.send_json(message)
                except Exception as e:
                    logger.error(f"Error broadcasting: {e}")

    async def broadcast_typing(self, conversation_id: str, is_typing: bool):
        await self.broadcast(conversation_id, {
            "type": "typing",
            "is_typing": is_typing,
            "timestamp": datetime.utcnow().isoformat()
        })


manager = ConnectionManager()


@router.websocket("/ws/chat/{conversation_id}")
async def websocket_endpoint(websocket: WebSocket, conversation_id: str):
    """WebSocket endpoint for real-time chat"""
    await manager.connect(websocket, conversation_id)

    try:
        while True:
            data = await websocket.receive_text()
            message_data = json.loads(data)

            # Handle typing indicator
            if message_data.get("type") == "typing":
                await manager.broadcast_typing(conversation_id, True)
                continue

            # Handle chat message
            if message_data.get("type") == "message":
                user_message = message_data.get("content", "").strip()
                user_id = message_data.get("user_id", "anonymous")

                if not user_message:
                    continue

                # Save user message
                manager.db.save_message(
                    conversation_id=conversation_id,
                    role="user",
                    content=user_message,
                    user_id=user_id
                )

                # Broadcast user message to all clients
                await manager.broadcast(conversation_id, {
                    "type": "message",
                    "role": "user",
                    "content": user_message,
                    "timestamp": datetime.utcnow().isoformat()
                })

                # Show typing indicator
                await manager.broadcast_typing(conversation_id, True)

                # Generate response
                try:
                    docs_text, sources = manager.rag.retrieve(user_message, top_k=4)
                    bot_response = manager.llm.generate_response(user_message, docs_text)
                    source_type = "document" if sources else "web"
                    confidence = "high" if sources else "medium"

                except Exception as e:
                    logger.error(f"Error generating response: {e}")
                    bot_response = f"I encountered an error: {str(e)[:100]}"
                    sources = []
                    source_type = "error"
                    confidence = "low"

                # Save bot message
                manager.db.save_message(
                    conversation_id=conversation_id,
                    role="bot",
                    content=bot_response,
                    user_id=user_id,
                    metadata={
                        "source_type": source_type,
                        "confidence": confidence,
                        "sources": sources or []
                    }
                )

                # Hide typing indicator
                await manager.broadcast_typing(conversation_id, False)

                # Broadcast bot response
                await manager.broadcast(conversation_id, {
                    "type": "message",
                    "role": "bot",
                    "content": bot_response,
                    "metadata": {
                        "source_type": source_type,
                        "confidence": confidence,
                        "sources": sources or []
                    },
                    "timestamp": datetime.utcnow().isoformat()
                })

    except WebSocketDisconnect:
        manager.disconnect(conversation_id, websocket)
        logger.info(f"WebSocket disconnected: {conversation_id}")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        manager.disconnect(conversation_id, websocket)
