# Database Service for Conversation Persistence
import logging
from typing import List, Optional
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from app.models.conversation import Base, Conversation, Message
from app.core.config import settings
from datetime import datetime

logger = logging.getLogger(__name__)

class DatabaseService:
    def __init__(self):
        try:
            # Create engine from DATABASE_URL in .env
            self.engine = create_engine(
                settings.database_url,
                echo=False,
                pool_pre_ping=True,  # Test connections before using
                pool_recycle=3600  # Recycle connections every hour
            )

            # Create tables
            Base.metadata.create_all(bind=self.engine)

            # Create session factory
            self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)

            logger.info("Database service initialized successfully")
            self.is_connected = True

        except Exception as e:
            logger.error(f"Failed to initialize database: {e}")
            self.is_connected = False
            self.engine = None
            self.SessionLocal = None

    def get_db_session(self) -> Optional[Session]:
        """Get a database session"""
        if not self.is_connected or not self.SessionLocal:
            return None
        try:
            return self.SessionLocal()
        except Exception as e:
            logger.error(f"Failed to create database session: {e}")
            return None

    def save_message(self, conversation_id: str, role: str, content: str,
                    user_id: str = "unknown", metadata: dict = None) -> bool:
        """Save a message to database"""
        if not self.is_connected:
            logger.warning("Database not connected, skipping message save")
            return False

        session = self.get_db_session()
        if not session:
            return False

        try:
            # Get or create conversation
            conversation = session.query(Conversation).filter(
                Conversation.conversation_id == conversation_id
            ).first()

            if not conversation:
                conversation = Conversation(
                    conversation_id=conversation_id,
                    user_id=user_id
                )
                session.add(conversation)

            # Create message
            message = Message(
                conversation_id=conversation_id,
                role=role,
                content=content,
                message_metadata=metadata or {}
            )
            session.add(message)

            # Update conversation
            conversation.updated_at = datetime.utcnow()
            conversation.message_count += 1

            # Set title from first user message
            if conversation.title is None and role == "user":
                conversation.title = content[:100] + ("..." if len(content) > 100 else "")

            session.commit()
            logger.debug(f"Saved message to conversation {conversation_id}")
            return True

        except Exception as e:
            logger.error(f"Error saving message: {e}")
            session.rollback()
            return False
        finally:
            session.close()

    def get_conversation(self, conversation_id: str) -> Optional[dict]:
        """Retrieve full conversation with all messages"""
        if not self.is_connected:
            logger.warning("Database not connected")
            return None

        session = self.get_db_session()
        if not session:
            return None

        try:
            conversation = session.query(Conversation).filter(
                Conversation.conversation_id == conversation_id
            ).first()

            if not conversation:
                logger.warning(f"Conversation not found: {conversation_id}")
                return None

            messages = session.query(Message).filter(
                Message.conversation_id == conversation_id
            ).order_by(Message.timestamp).all()

            return {
                "conversation_id": conversation.conversation_id,
                "user_id": conversation.user_id,
                "created_at": conversation.created_at.isoformat() if conversation.created_at else None,
                "updated_at": conversation.updated_at.isoformat() if conversation.updated_at else None,
                "title": conversation.title,
                "message_count": conversation.message_count,
                "messages": [msg.to_dict() for msg in messages]
            }

        except Exception as e:
            logger.error(f"Error retrieving conversation: {e}")
            return None
        finally:
            session.close()

    def list_conversations(self, user_id: str = None, limit: int = 50) -> List[dict]:
        """List conversations (optionally filtered by user)"""
        if not self.is_connected:
            logger.warning("Database not connected")
            return []

        session = self.get_db_session()
        if not session:
            return []

        try:
            query = session.query(Conversation)

            if user_id:
                query = query.filter(Conversation.user_id == user_id)

            conversations = query.order_by(
                Conversation.updated_at.desc()
            ).limit(limit).all()

            return [conv.to_dict() for conv in conversations]

        except Exception as e:
            logger.error(f"Error listing conversations: {e}")
            return []
        finally:
            session.close()

    def delete_conversation(self, conversation_id: str) -> bool:
        """Delete a conversation and all its messages"""
        if not self.is_connected:
            return False

        session = self.get_db_session()
        if not session:
            return False

        try:
            # Delete all messages
            session.query(Message).filter(
                Message.conversation_id == conversation_id
            ).delete()

            # Delete conversation
            session.query(Conversation).filter(
                Conversation.conversation_id == conversation_id
            ).delete()

            session.commit()
            logger.info(f"Deleted conversation: {conversation_id}")
            return True

        except Exception as e:
            logger.error(f"Error deleting conversation: {e}")
            session.rollback()
            return False
        finally:
            session.close()

    def search_messages(self, query: str, limit: int = 20) -> List[dict]:
        """Search messages by content"""
        if not self.is_connected:
            logger.warning("Database not connected")
            return []

        session = self.get_db_session()
        if not session:
            return []

        try:
            messages = session.query(Message).filter(
                Message.content.ilike(f"%{query}%")
            ).order_by(Message.timestamp.desc()).limit(limit).all()

            return [msg.to_dict() for msg in messages]

        except Exception as e:
            logger.error(f"Error searching messages: {e}")
            return []
        finally:
            session.close()

    def get_user_conversations(self, user_id: str, limit: int = 50) -> List[dict]:
        """Get conversations for a specific user"""
        if not self.is_connected:
            return []

        session = self.get_db_session()
        if not session:
            return []

        try:
            conversations = session.query(Conversation).filter(
                Conversation.user_id == user_id
            ).order_by(Conversation.updated_at.desc()).limit(limit).all()

            return [conv.to_dict() for conv in conversations]

        except Exception as e:
            logger.error(f"Error getting user conversations: {e}")
            return []
        finally:
            session.close()

    def test_connection(self) -> bool:
        """Test database connection"""
        if not self.is_connected:
            return False

        session = self.get_db_session()
        if not session:
            return False

        try:
            session.execute("SELECT 1")
            logger.info("Database connection test successful")
            return True
        except Exception as e:
            logger.error(f"Database connection test failed: {e}")
            return False
        finally:
            session.close()
