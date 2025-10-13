"""
Chat history manager
"""
import os
import json
from datetime import datetime
from typing import List, Dict

class ChatManager:
    """Manages chat conversations and history"""

    def __init__(self, chats_dir="./data/chats"):
        self.chats_dir = chats_dir
        os.makedirs(chats_dir, exist_ok=True)

    def create_chat(self, title: str = "New Chat") -> Dict:
        """Create a new chat"""
        chat_id = f"chat_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        chat = {
            'id': chat_id,
            'title': title,
            'messages': [],
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat()
        }
        self.save_chat(chat)
        return chat

    def save_chat(self, chat: Dict):
        """Save chat to file"""
        chat['updated_at'] = datetime.now().isoformat()
        chat_file = os.path.join(self.chats_dir, f"{chat['id']}.json")
        with open(chat_file, 'w') as f:
            json.dump(chat, f, indent=2)

    def load_chat(self, chat_id: str) -> Dict:
        """Load a chat by ID"""
        chat_file = os.path.join(self.chats_dir, f"{chat_id}.json")
        if os.path.exists(chat_file):
            with open(chat_file, 'r') as f:
                return json.load(f)
        return None

    def get_all_chats(self) -> List[Dict]:
        """Get all chats (metadata only)"""
        chats = []
        for filename in os.listdir(self.chats_dir):
            if filename.endswith('.json'):
                chat_file = os.path.join(self.chats_dir, filename)
                with open(chat_file, 'r') as f:
                    chat = json.load(f)
                    # Return metadata only
                    chats.append({
                        'id': chat['id'],
                        'title': chat['title'],
                        'message_count': len(chat['messages']),
                        'created_at': chat['created_at'],
                        'updated_at': chat['updated_at']
                    })
        # Sort by updated time
        chats.sort(key=lambda x: x['updated_at'], reverse=True)
        return chats

    def add_message(self, chat_id: str, role: str, content: str):
        """Add a message to a chat"""
        chat = self.load_chat(chat_id)
        if not chat:
            return None

        message = {
            'role': role,
            'content': content,
            'timestamp': datetime.now().isoformat()
        }
        chat['messages'].append(message)

        # Auto-update title from first user message
        if len(chat['messages']) == 1 and role == 'user':
            chat['title'] = content[:50] + ('...' if len(content) > 50 else '')

        self.save_chat(chat)
        return chat

    def delete_chat(self, chat_id: str):
        """Delete a chat"""
        chat_file = os.path.join(self.chats_dir, f"{chat_id}.json")
        if os.path.exists(chat_file):
            os.remove(chat_file)

    def get_chat_history_for_llm(self, chat_id: str, max_messages: int = 10) -> List[Dict]:
        """Get chat history formatted for LLM"""
        chat = self.load_chat(chat_id)
        if not chat:
            return []

        # Return last N messages
        messages = chat['messages'][-max_messages:]
        return [{'role': msg['role'], 'content': msg['content']} for msg in messages]
