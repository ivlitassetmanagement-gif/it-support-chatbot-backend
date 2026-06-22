# Conversation History Service
# Stores chat history locally (no database needed)

import json
import os
from datetime import datetime
from typing import List, Dict, Optional
import logging

logger = logging.getLogger(__name__)

class ConversationService:
    def __init__(self, storage_dir: str = "./storage/conversations"):
        self.storage_dir = storage_dir

        # Create storage directory if it doesn't exist
        if not os.path.exists(storage_dir):
            os.makedirs(storage_dir, exist_ok=True)
            logger.info(f"Created conversation storage: {storage_dir}")

    def get_conversation_file(self, conversation_id: str) -> str:
        """Get the file path for a conversation"""
        return os.path.join(self.storage_dir, f"{conversation_id}.json")

    def save_message(self, conversation_id: str, role: str, content: str,
                     metadata: Optional[Dict] = None) -> Dict:
        """Save a single message to conversation history"""
        try:
            file_path = self.get_conversation_file(conversation_id)

            # Load existing conversation or create new one
            if os.path.exists(file_path):
                with open(file_path, 'r', encoding='utf-8') as f:
                    conversation = json.load(f)
            else:
                conversation = {
                    "conversation_id": conversation_id,
                    "created_at": datetime.now().isoformat(),
                    "messages": []
                }

            # Add new message
            message = {
                "timestamp": datetime.now().isoformat(),
                "role": role,  # "user" or "bot"
                "content": content,
                "metadata": metadata or {}
            }

            conversation["messages"].append(message)
            conversation["updated_at"] = datetime.now().isoformat()

            # Save to file
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(conversation, f, indent=2, ensure_ascii=False)

            logger.debug(f"Saved message to conversation {conversation_id}")
            return message

        except Exception as e:
            logger.error(f"Error saving message: {e}")
            raise

    def get_conversation(self, conversation_id: str) -> Optional[Dict]:
        """Retrieve full conversation history"""
        try:
            file_path = self.get_conversation_file(conversation_id)

            if not os.path.exists(file_path):
                logger.warning(f"Conversation not found: {conversation_id}")
                return None

            with open(file_path, 'r', encoding='utf-8') as f:
                conversation = json.load(f)

            return conversation

        except Exception as e:
            logger.error(f"Error retrieving conversation: {e}")
            raise

    def list_conversations(self, limit: int = 50) -> List[Dict]:
        """List all conversations (most recent first)"""
        try:
            conversations = []

            for filename in os.listdir(self.storage_dir):
                if filename.endswith('.json'):
                    file_path = os.path.join(self.storage_dir, filename)
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            conv = json.load(f)
                            conversations.append({
                                "conversation_id": conv.get("conversation_id"),
                                "created_at": conv.get("created_at"),
                                "updated_at": conv.get("updated_at"),
                                "message_count": len(conv.get("messages", []))
                            })
                    except Exception as e:
                        logger.error(f"Error reading {filename}: {e}")

            # Sort by updated_at (most recent first)
            conversations.sort(key=lambda x: x.get("updated_at", ""), reverse=True)

            return conversations[:limit]

        except Exception as e:
            logger.error(f"Error listing conversations: {e}")
            return []

    def delete_conversation(self, conversation_id: str) -> bool:
        """Delete a conversation"""
        try:
            file_path = self.get_conversation_file(conversation_id)

            if os.path.exists(file_path):
                os.remove(file_path)
                logger.info(f"Deleted conversation: {conversation_id}")
                return True

            logger.warning(f"Conversation not found: {conversation_id}")
            return False

        except Exception as e:
            logger.error(f"Error deleting conversation: {e}")
            raise

    def clear_old_conversations(self, days: int = 30) -> int:
        """Delete conversations older than specified days"""
        try:
            from datetime import timedelta

            cutoff_date = datetime.now() - timedelta(days=days)
            deleted_count = 0

            for filename in os.listdir(self.storage_dir):
                if filename.endswith('.json'):
                    file_path = os.path.join(self.storage_dir, filename)
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            conv = json.load(f)
                            updated_at = datetime.fromisoformat(conv.get("updated_at", ""))

                            if updated_at < cutoff_date:
                                os.remove(file_path)
                                deleted_count += 1
                    except Exception as e:
                        logger.error(f"Error processing {filename}: {e}")

            if deleted_count > 0:
                logger.info(f"Cleaned up {deleted_count} old conversations")

            return deleted_count

        except Exception as e:
            logger.error(f"Error clearing old conversations: {e}")
            return 0
