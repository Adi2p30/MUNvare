"""
Memory Manager - Tracks notes, changes, and system state for LLM context
"""
import json
import os
from datetime import datetime
from typing import Dict, Any, List, Optional
from pathlib import Path


class MemoryManager:
    """
    Manages system memory including notes, changes, and important context.
    Creates compact summaries for LLM context.
    """

    def __init__(self, memory_dir: str = "data/memory"):
        """
        Initialize memory manager.

        Args:
            memory_dir: Directory to store memory files
        """
        self.memory_dir = Path(memory_dir)
        self.memory_dir.mkdir(parents=True, exist_ok=True)

        self.memory_file = self.memory_dir / "system_memory.json"
        self.changes_file = self.memory_dir / "recent_changes.json"

        # Initialize or load memory
        self.memory = self._load_memory()
        self.changes = self._load_changes()

    def _load_memory(self) -> Dict[str, Any]:
        """Load memory from file or create new."""
        if self.memory_file.exists():
            try:
                with open(self.memory_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                print(f"Error loading memory: {e}")

        # Default memory structure
        return {
            'notes_summary': {},
            'research_history': [],
            'user_preferences': {},
            'session_context': {},
            'last_updated': datetime.now().isoformat()
        }

    def _load_changes(self) -> List[Dict[str, Any]]:
        """Load recent changes from file."""
        if self.changes_file.exists():
            try:
                with open(self.changes_file, 'r') as f:
                    changes = json.load(f)
                    # Keep only last 50 changes
                    return changes[-50:]
            except Exception as e:
                print(f"Error loading changes: {e}")
        return []

    def _save_memory(self):
        """Save memory to file."""
        try:
            self.memory['last_updated'] = datetime.now().isoformat()
            with open(self.memory_file, 'w') as f:
                json.dump(self.memory, f, indent=2)
        except Exception as e:
            print(f"Error saving memory: {e}")

    def _save_changes(self):
        """Save changes to file."""
        try:
            with open(self.changes_file, 'w') as f:
                json.dump(self.changes, f, indent=2)
        except Exception as e:
            print(f"Error saving changes: {e}")

    def track_note_created(self, note_id: str, title: str, folder: str, content_preview: str):
        """
        Track when a note is created.

        Args:
            note_id: Note ID
            title: Note title
            folder: Folder name
            content_preview: First 200 chars of content
        """
        change = {
            'type': 'note_created',
            'timestamp': datetime.now().isoformat(),
            'note_id': note_id,
            'title': title,
            'folder': folder,
            'preview': content_preview[:200]
        }
        self.changes.append(change)

        # Update notes summary
        if folder not in self.memory['notes_summary']:
            self.memory['notes_summary'][folder] = []

        self.memory['notes_summary'][folder].append({
            'id': note_id,
            'title': title,
            'created': datetime.now().isoformat(),
            'preview': content_preview[:200]
        })

        self._save_changes()
        self._save_memory()

    def track_note_updated(self, note_id: str, title: str, changes_description: str):
        """Track when a note is updated."""
        change = {
            'type': 'note_updated',
            'timestamp': datetime.now().isoformat(),
            'note_id': note_id,
            'title': title,
            'changes': changes_description
        }
        self.changes.append(change)
        self._save_changes()

    def track_research_completed(self, research_type: str, country: str, topic: str, result_summary: str):
        """
        Track completed research.

        Args:
            research_type: Type of research
            country: Country researched
            topic: Topic researched
            result_summary: Summary of results
        """
        change = {
            'type': 'research_completed',
            'timestamp': datetime.now().isoformat(),
            'research_type': research_type,
            'country': country,
            'topic': topic,
            'summary': result_summary[:300]
        }
        self.changes.append(change)

        # Add to research history
        self.memory['research_history'].append({
            'type': research_type,
            'country': country,
            'topic': topic,
            'timestamp': datetime.now().isoformat(),
            'summary': result_summary[:300]
        })

        # Keep only last 20 research items
        self.memory['research_history'] = self.memory['research_history'][-20:]

        self._save_changes()
        self._save_memory()

    def track_agent_execution(self, agent_name: str, task: str, success: bool):
        """Track agent execution."""
        change = {
            'type': 'agent_execution',
            'timestamp': datetime.now().isoformat(),
            'agent': agent_name,
            'task': task,
            'success': success
        }
        self.changes.append(change)
        self._save_changes()

    def update_session_context(self, context_update: Dict[str, Any]):
        """
        Update session context.

        Args:
            context_update: Dictionary of context to update
        """
        self.memory['session_context'].update(context_update)
        self._save_memory()

    def get_compact_memory_for_llm(self, max_tokens: int = 500) -> str:
        """
        Generate compact memory summary for LLM context.

        Args:
            max_tokens: Maximum tokens for memory (approximate)

        Returns:
            Compact memory string
        """
        memory_parts = []

        # Recent changes (last 10)
        recent_changes = self.changes[-10:]
        if recent_changes:
            memory_parts.append("## Recent Activity")
            for change in recent_changes[-5:]:  # Last 5
                if change['type'] == 'note_created':
                    memory_parts.append(f"- Created note: {change['title']} in {change['folder']}")
                elif change['type'] == 'research_completed':
                    memory_parts.append(f"- Researched: {change['country']} on {change['topic']}")
                elif change['type'] == 'note_updated':
                    memory_parts.append(f"- Updated note: {change['title']}")

        # Notes summary by folder
        if self.memory['notes_summary']:
            memory_parts.append("\n## Available Notes")
            for folder, notes in self.memory['notes_summary'].items():
                memory_parts.append(f"- {folder}: {len(notes)} notes")
                # List most recent 3 notes per folder
                for note in notes[-3:]:
                    memory_parts.append(f"  * {note['title']}")

        # Research history summary
        if self.memory['research_history']:
            memory_parts.append("\n## Recent Research")
            unique_topics = {}
            for research in self.memory['research_history'][-10:]:
                key = f"{research['country']} - {research['topic']}"
                unique_topics[key] = research['type']

            for topic, rtype in list(unique_topics.items())[-5:]:
                memory_parts.append(f"- {topic} ({rtype})")

        # Session context
        if self.memory['session_context']:
            memory_parts.append("\n## Session Context")
            if 'current_country' in self.memory['session_context']:
                memory_parts.append(f"- Country: {self.memory['session_context']['current_country']}")
            if 'current_topic' in self.memory['session_context']:
                memory_parts.append(f"- Topic: {self.memory['session_context']['current_topic']}")
            if 'committee' in self.memory['session_context']:
                memory_parts.append(f"- Committee: {self.memory['session_context']['committee']}")

        compact_memory = "\n".join(memory_parts)

        # Truncate if too long (rough estimate: 4 chars per token)
        max_chars = max_tokens * 4
        if len(compact_memory) > max_chars:
            compact_memory = compact_memory[:max_chars] + "..."

        return compact_memory

    def get_relevant_notes_context(self, query: str, max_notes: int = 5) -> str:
        """
        Get relevant notes based on query.

        Args:
            query: Search query
            max_notes: Maximum notes to return

        Returns:
            Context string with relevant notes
        """
        query_lower = query.lower()
        relevant_notes = []

        for folder, notes in self.memory['notes_summary'].items():
            for note in notes:
                # Simple relevance scoring
                score = 0
                if query_lower in note['title'].lower():
                    score += 10
                if query_lower in note['preview'].lower():
                    score += 5

                if score > 0:
                    relevant_notes.append((score, note))

        # Sort by score and take top notes
        relevant_notes.sort(reverse=True, key=lambda x: x[0])
        top_notes = [note for score, note in relevant_notes[:max_notes]]

        if not top_notes:
            return ""

        context_parts = ["## Relevant Notes from Your Library"]
        for note in top_notes:
            context_parts.append(f"\n**{note['title']}**")
            context_parts.append(note['preview'])

        return "\n".join(context_parts)

    def get_research_history_for_topic(self, country: str, topic: str) -> str:
        """Get previous research on same country/topic."""
        relevant_research = []

        for research in self.memory['research_history']:
            if research['country'].lower() == country.lower():
                if topic.lower() in research['topic'].lower():
                    relevant_research.append(research)

        if not relevant_research:
            return ""

        context_parts = [f"## Previous Research on {country} - {topic}"]
        for research in relevant_research[-3:]:  # Last 3 relevant
            context_parts.append(f"\n**{research['type']}** ({research['timestamp'][:10]})")
            context_parts.append(research['summary'])

        return "\n".join(context_parts)

    def clear_old_changes(self, days: int = 7):
        """Clear changes older than specified days."""
        cutoff = datetime.now().timestamp() - (days * 24 * 60 * 60)
        self.changes = [
            c for c in self.changes
            if datetime.fromisoformat(c['timestamp']).timestamp() > cutoff
        ]
        self._save_changes()

    def get_statistics(self) -> Dict[str, Any]:
        """Get memory statistics."""
        total_notes = sum(len(notes) for notes in self.memory['notes_summary'].values())

        return {
            'total_notes': total_notes,
            'folders': len(self.memory['notes_summary']),
            'research_items': len(self.memory['research_history']),
            'recent_changes': len(self.changes),
            'last_updated': self.memory.get('last_updated', 'Unknown')
        }
