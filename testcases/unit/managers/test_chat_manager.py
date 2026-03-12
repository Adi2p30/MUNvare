"""
Unit tests for Chat Manager
Tests chat conversation management
"""
import pytest
import json
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..', 'backend'))


class TestChatManager:
    """Test Chat Manager functionality"""

    def test_create_chat(self, temp_data_dir):
        """Test creating a new chat"""
        from managers.chat_manager import ChatManager

        manager = ChatManager(data_dir=str(temp_data_dir / 'chats'))

        chat = manager.create_chat()

        assert chat is not None
        assert 'id' in chat
        assert 'messages' in chat
        assert isinstance(chat['messages'], list)
        assert len(chat['messages']) == 0

    def test_add_message_to_chat(self, temp_data_dir):
        """Test adding messages to a chat"""
        from managers.chat_manager import ChatManager

        manager = ChatManager(data_dir=str(temp_data_dir / 'chats'))

        chat = manager.create_chat()
        chat_id = chat['id']

        updated_chat = manager.add_message(
            chat_id,
            role="user",
            content="Hello, how can you help me?"
        )

        assert len(updated_chat['messages']) == 1
        assert updated_chat['messages'][0]['role'] == "user"
        assert updated_chat['messages'][0]['content'] == "Hello, how can you help me?"

    def test_get_chat_history(self, temp_data_dir):
        """Test retrieving chat history"""
        from managers.chat_manager import ChatManager

        manager = ChatManager(data_dir=str(temp_data_dir / 'chats'))

        chat = manager.create_chat()
        chat_id = chat['id']

        manager.add_message(chat_id, "user", "Message 1")
        manager.add_message(chat_id, "assistant", "Response 1")
        manager.add_message(chat_id, "user", "Message 2")

        chat_history = manager.get_chat(chat_id)

        assert len(chat_history['messages']) == 3

    def test_delete_chat(self, temp_data_dir):
        """Test deleting a chat"""
        from managers.chat_manager import ChatManager

        manager = ChatManager(data_dir=str(temp_data_dir / 'chats'))

        chat = manager.create_chat()
        chat_id = chat['id']

        manager.delete_chat(chat_id)

        all_chats = manager.get_all_chats()
        assert not any(c['id'] == chat_id for c in all_chats)

    def test_get_all_chats(self, temp_data_dir):
        """Test retrieving all chats"""
        from managers.chat_manager import ChatManager

        manager = ChatManager(data_dir=str(temp_data_dir / 'chats'))

        chat1 = manager.create_chat()
        chat2 = manager.create_chat()

        all_chats = manager.get_all_chats()

        assert len(all_chats) == 2

    def test_chat_persistence(self, temp_data_dir):
        """Test that chats persist to disk"""
        from managers.chat_manager import ChatManager

        manager = ChatManager(data_dir=str(temp_data_dir / 'chats'))

        chat = manager.create_chat()
        chat_id = chat['id']
        manager.add_message(chat_id, "user", "Test message")

        # Create new manager instance to test persistence
        manager2 = ChatManager(data_dir=str(temp_data_dir / 'chats'))
        loaded_chat = manager2.get_chat(chat_id)

        assert loaded_chat is not None
        assert len(loaded_chat['messages']) == 1
        assert loaded_chat['messages'][0]['content'] == "Test message"
