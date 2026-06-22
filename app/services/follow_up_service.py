"""Service for generating follow-up questions using LLM"""
import logging
from typing import List
from app.services.llm_service import LLMService

logger = logging.getLogger(__name__)


class FollowUpQuestionService:
    """Generate intelligent follow-up questions based on conversation context"""

    def __init__(self):
        self.llm = LLMService()

    def generate_follow_up_questions(
        self,
        user_message: str,
        assistant_response: str,
        num_questions: int = 5,
    ) -> List[str]:
        """
        Generate interactive, context-aware follow-up questions based on the conversation.

        Args:
            user_message: The user's original question
            assistant_response: The AI's response
            num_questions: Number of questions to generate (default: 5)

        Returns:
            List of follow-up question suggestions
        """
        try:
            prompt = f"""As an IT support assistant, generate {num_questions} SPECIFIC follow-up questions that naturally continue this conversation.

ORIGINAL USER QUESTION: "{user_message}"

YOUR RESPONSE: "{assistant_response}"

REQUIREMENTS FOR FOLLOW-UP QUESTIONS:
1. Be specific and actionable - not generic
2. Address common next steps or potential issues
3. Help the user troubleshoot further or understand better
4. Sound natural and conversational
5. Keep each under 12 words
6. Focus on:
   - Clarifying details if the solution had steps
   - Troubleshooting if something went wrong
   - Related features or policies
   - Prevention of future issues
   - "What if?" scenarios

RETURN ONLY the questions, one per line, no numbering or bullets:"""

            response = self.llm.generate_response(prompt, context="")

            # Parse the response into individual questions
            questions = [
                q.strip()
                for q in response.split('\n')
                if q.strip() and len(q.strip()) > 8 and not q.strip().startswith(('1', '2', '3', '4', '5', '6', '7', '8', '9', '0', '-', '*', '•'))
            ]

            # Limit to requested number
            return questions[:num_questions] if questions else self._get_default_questions(user_message)

        except Exception as e:
            logger.error(f"Error generating follow-up questions: {e}")
            return self._get_default_questions(user_message)

    def _get_default_questions(self, user_message: str) -> List[str]:
        """
        Provide intelligent default follow-up questions as fallback.
        Adapted based on the type of user question.

        Args:
            user_message: The original user question

        Returns:
            List of contextual default follow-up questions
        """
        # Detect question type to provide better defaults
        lower_msg = user_message.lower()

        if any(word in lower_msg for word in ["error", "issue", "problem", "not working", "can't", "cannot"]):
            # Troubleshooting-focused defaults
            return [
                "What error message do you see exactly?",
                "Have you tried restarting your device?",
                "Does this work on a different device?",
                "When did this issue start happening?",
                "Have you contacted IT Support yet?",
            ]
        elif any(word in lower_msg for word in ["policy", "procedure", "guideline", "rule", "requirement", "password", "security"]):
            # Policy-focused defaults
            return [
                "Does this policy apply to my situation?",
                "What happens if I don't follow this?",
                "Are there any exceptions to this policy?",
                "How often do I need to do this?",
                "Who enforces this policy?",
            ]
        elif any(word in lower_msg for word in ["how", "setup", "configure", "install", "access", "use"]):
            # How-to/Setup defaults
            return [
                "Where can I find detailed step-by-step instructions?",
                "What if I get stuck on a particular step?",
                "Is there a faster way to do this?",
                "How long does this usually take?",
                "Who can help if I need support?",
            ]
        else:
            # General defaults
            return [
                "Can you provide more specific details?",
                "Is there anything else I can help with?",
                "Where can I find more information about this?",
                "Who should I contact for additional help?",
                "What should I do if this changes?",
            ]

    def generate_contextual_questions(
        self,
        message_history: List[dict],
        num_questions: int = 3,
    ) -> List[str]:
        """
        Generate follow-up questions based on full conversation history.

        Args:
            message_history: List of previous messages in conversation
            num_questions: Number of questions to generate

        Returns:
            List of contextual follow-up questions
        """
        try:
            # Build conversation context
            conversation_context = "\n".join(
                [
                    f"{msg['role'].upper()}: {msg['content'][:200]}"
                    for msg in message_history[-5:]  # Last 5 messages for context
                ]
            )

            prompt = f"""Based on this conversation history, what are {num_questions} good follow-up questions
the user might ask next? Think about natural next steps and clarifications they might need.

Conversation:
{conversation_context}

Generate {num_questions} follow-up questions that would help the user continue the conversation naturally.
Return ONLY the questions, one per line, without numbering:"""

            response = self.llm.generate_response(prompt, context="")

            questions = [
                q.strip()
                for q in response.split('\n')
                if q.strip() and len(q.strip()) > 10
            ]

            return questions[:num_questions]

        except Exception as e:
            logger.error(f"Error generating contextual questions: {e}")
            return self._get_default_questions("")
