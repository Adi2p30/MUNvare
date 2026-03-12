"""
Committee Flow Manager
Manages committee session flow with different debate building blocks
"""
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional


class CommitteeFlowManager:
    """Manages committee flow and debate building blocks"""

    def __init__(self, data_dir: str = None):
        if data_dir is None:
            self.data_dir = Path(__file__).parent.parent.parent / 'data' / 'committee_flows'
        else:
            self.data_dir = Path(data_dir) / 'committee_flows'

        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.flows_file = self.data_dir / 'flows.json'

        # Initialize flows file if it doesn't exist
        if not self.flows_file.exists():
            self._save_flows([])

    def _load_flows(self) -> List[Dict]:
        """Load all committee flows"""
        try:
            with open(self.flows_file, 'r') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return []

    def _save_flows(self, flows: List[Dict]):
        """Save committee flows"""
        with open(self.flows_file, 'w') as f:
            json.dump(flows, f, indent=2)

    def create_flow(self, name: str, session_id: str = None) -> Dict:
        """Create a new committee flow"""
        flows = self._load_flows()

        flow_id = f"flow_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        flow = {
            'id': flow_id,
            'name': name,
            'session_id': session_id,
            'blocks': [],
            'current_block_index': None,
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat(),
            'status': 'active'  # active, paused, completed
        }

        flows.append(flow)
        self._save_flows(flows)

        return flow

    def get_flow(self, flow_id: str) -> Optional[Dict]:
        """Get a specific flow"""
        flows = self._load_flows()
        for flow in flows:
            if flow['id'] == flow_id:
                return flow
        return None

    def get_all_flows(self, session_id: str = None) -> List[Dict]:
        """Get all flows, optionally filtered by session"""
        flows = self._load_flows()
        if session_id:
            return [f for f in flows if f.get('session_id') == session_id]
        return flows

    def update_flow(self, flow_id: str, **kwargs) -> Optional[Dict]:
        """Update flow properties"""
        flows = self._load_flows()

        for flow in flows:
            if flow['id'] == flow_id:
                for key, value in kwargs.items():
                    if key in flow:
                        flow[key] = value
                flow['updated_at'] = datetime.now().isoformat()
                self._save_flows(flows)
                return flow

        return None

    def delete_flow(self, flow_id: str) -> bool:
        """Delete a flow"""
        flows = self._load_flows()
        flows = [f for f in flows if f['id'] != flow_id]
        self._save_flows(flows)
        return True

    def add_block(self, flow_id: str, block_type: str, block_data: Dict) -> Optional[Dict]:
        """Add a building block to the flow"""
        flows = self._load_flows()

        for flow in flows:
            if flow['id'] == flow_id:
                block_id = f"block_{len(flow['blocks']) + 1}_{datetime.now().strftime('%H%M%S')}"

                block = {
                    'id': block_id,
                    'type': block_type,
                    'data': block_data,
                    'status': 'pending',  # pending, active, completed
                    'created_at': datetime.now().isoformat(),
                    'started_at': None,
                    'completed_at': None,
                    'notes': []
                }

                flow['blocks'].append(block)
                flow['updated_at'] = datetime.now().isoformat()
                self._save_flows(flows)

                return block

        return None

    def update_block(self, flow_id: str, block_id: str, **kwargs) -> Optional[Dict]:
        """Update a specific block"""
        flows = self._load_flows()

        for flow in flows:
            if flow['id'] == flow_id:
                for block in flow['blocks']:
                    if block['id'] == block_id:
                        for key, value in kwargs.items():
                            if key in block:
                                block[key] = value
                        flow['updated_at'] = datetime.now().isoformat()
                        self._save_flows(flows)
                        return block

        return None

    def delete_block(self, flow_id: str, block_id: str) -> bool:
        """Delete a block from the flow"""
        flows = self._load_flows()

        for flow in flows:
            if flow['id'] == flow_id:
                flow['blocks'] = [b for b in flow['blocks'] if b['id'] != block_id]
                flow['updated_at'] = datetime.now().isoformat()
                self._save_flows(flows)
                return True

        return False

    def reorder_blocks(self, flow_id: str, block_order: List[str]) -> bool:
        """Reorder blocks in the flow"""
        flows = self._load_flows()

        for flow in flows:
            if flow['id'] == flow_id:
                # Create new ordered list
                new_blocks = []
                for block_id in block_order:
                    for block in flow['blocks']:
                        if block['id'] == block_id:
                            new_blocks.append(block)
                            break

                flow['blocks'] = new_blocks
                flow['updated_at'] = datetime.now().isoformat()
                self._save_flows(flows)
                return True

        return False

    def start_block(self, flow_id: str, block_id: str) -> Optional[Dict]:
        """Mark a block as active/started"""
        flows = self._load_flows()

        for flow in flows:
            if flow['id'] == flow_id:
                for block in flow['blocks']:
                    if block['id'] == block_id:
                        block['status'] = 'active'
                        block['started_at'] = datetime.now().isoformat()

                        # Update current block index
                        flow['current_block_index'] = flow['blocks'].index(block)

                        flow['updated_at'] = datetime.now().isoformat()
                        self._save_flows(flows)
                        return block

        return None

    def complete_block(self, flow_id: str, block_id: str) -> Optional[Dict]:
        """Mark a block as completed"""
        flows = self._load_flows()

        for flow in flows:
            if flow['id'] == flow_id:
                for block in flow['blocks']:
                    if block['id'] == block_id:
                        block['status'] = 'completed'
                        block['completed_at'] = datetime.now().isoformat()
                        flow['updated_at'] = datetime.now().isoformat()
                        self._save_flows(flows)
                        return block

        return None

    def add_block_note(self, flow_id: str, block_id: str, note: str) -> Optional[Dict]:
        """Add a note to a specific block"""
        flows = self._load_flows()

        for flow in flows:
            if flow['id'] == flow_id:
                for block in flow['blocks']:
                    if block['id'] == block_id:
                        note_entry = {
                            'text': note,
                            'timestamp': datetime.now().isoformat()
                        }
                        block['notes'].append(note_entry)
                        flow['updated_at'] = datetime.now().isoformat()
                        self._save_flows(flows)
                        return block

        return None

    def get_block_templates(self) -> List[Dict]:
        """Get predefined block templates for different debate types"""
        return [
            {
                'id': 'gsl',
                'name': 'General Speakers List (GSL)',
                'icon': '🎤',
                'description': 'Formal debate where delegates speak in order',
                'default_data': {
                    'speaker_time': 90,
                    'speakers': [],
                    'total_time': None
                }
            },
            {
                'id': 'moderated_caucus',
                'name': 'Moderated Caucus',
                'icon': '💬',
                'description': 'Focused discussion on a specific sub-topic',
                'default_data': {
                    'topic': '',
                    'total_time': 10,
                    'speaker_time': 60,
                    'speakers': []
                }
            },
            {
                'id': 'unmoderated_caucus',
                'name': 'Unmoderated Caucus',
                'icon': '🗣️',
                'description': 'Informal discussion and negotiation time',
                'default_data': {
                    'duration': 10,
                    'purpose': 'Lobbying and drafting'
                }
            },
            {
                'id': 'crisis',
                'name': 'Crisis Update',
                'icon': '🚨',
                'description': 'Breaking news or crisis scenario',
                'default_data': {
                    'title': '',
                    'description': '',
                    'response_time': None
                }
            },
            {
                'id': 'resolution_discussion',
                'name': 'Resolution Discussion',
                'icon': '📜',
                'description': 'Debate on draft resolution',
                'default_data': {
                    'resolution_title': '',
                    'sponsors': [],
                    'status': 'discussion'
                }
            },
            {
                'id': 'amendment',
                'name': 'Amendment Discussion',
                'icon': '✏️',
                'description': 'Propose and vote on amendments',
                'default_data': {
                    'amendment_text': '',
                    'proposer': '',
                    'type': 'friendly'  # friendly or unfriendly
                }
            },
            {
                'id': 'voting',
                'name': 'Voting Procedure',
                'icon': '🗳️',
                'description': 'Vote on resolutions or amendments',
                'default_data': {
                    'motion': '',
                    'type': 'substantive',  # substantive or procedural
                    'votes': {
                        'for': 0,
                        'against': 0,
                        'abstain': 0
                    }
                }
            },
            {
                'id': 'consultation',
                'name': 'Consultation of the Whole',
                'icon': '🤝',
                'description': 'Informal setting to discuss and refine resolutions',
                'default_data': {
                    'duration': 15,
                    'purpose': ''
                }
            },
            {
                'id': 'right_of_reply',
                'name': 'Right of Reply',
                'icon': '↩️',
                'description': 'Response to allegations or personal attacks',
                'default_data': {
                    'country': '',
                    'responding_to': ''
                }
            },
            {
                'id': 'break',
                'name': 'Break',
                'icon': '☕',
                'description': 'Scheduled break time',
                'default_data': {
                    'duration': 15,
                    'type': 'break'  # break, lunch, etc.
                }
            }
        ]
