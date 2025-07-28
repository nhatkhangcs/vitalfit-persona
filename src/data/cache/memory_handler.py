"""
Memory Handler - Handle messages with short-term memory
Separate complex logic to make main code readable
"""

from src.data.cache.redis_cache import ShortTermMemory


class MessageMemoryHandler:
    def __init__(self, max_messages: int = 15, port: int = 6379):
        self.session_manager = ShortTermMemory(max_messages=max_messages, port=port)

    def get_history_message(self) -> str:
        """
        Get context from memory up to now

        Returns:
            str: History context retrieved
        """
        session_key = self.session_manager.get_session_key()
        context = self.session_manager.get_history_context(session_key)

        return context
    
    def store_user_message(self, content):
        """Store user message to memory"""
        session_key = self.session_manager.get_session_key()
        self.session_manager.update_message_count()
        self.session_manager.store_user_message(session_key, content)

    def store_bot_response(self, response: str):
        """Store bot response to memory"""
        session_key = self.session_manager.get_session_key()
        self.session_manager.store_bot_message(session_key, response)

    def store_error(self, error: Exception):
        """Store error to memory"""
        session_key = self.session_manager.get_session_key()
        self.session_manager.store_error_message(session_key, error)

    def clear_memory(self):
        return self.session_manager.clear_cache()
