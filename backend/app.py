from flask import Flask, request, jsonify, send_from_directory, send_file
from flask_cors import CORS
import os
import json
import uuid
from datetime import datetime
from io import BytesIO
import markdown2
from core.vectordb import initialize_vector_db
from core.ai_service import AIService
from managers.config_manager import ConfigManager
from managers.chat_manager import ChatManager
from managers.notes_manager import NotesManager
from managers.session_manager import SessionManager
from managers.committee_flow_manager import CommitteeFlowManager
from agents import AgentOrchestrator
from realtime.socket_manager import init_socketio, register_events, socketio
import sys

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

app = Flask(__name__, static_folder='../frontend', static_url_path='')
CORS(app)

# Initialize SocketIO
init_socketio(app)
register_events(socketio)

# Initialize services
print("Initializing vector database...")
vectordb = initialize_vector_db()

print("Initializing AI service...")
ai_service = AIService(vectordb)

print("Initializing configuration manager...")
config_manager = ConfigManager()

print("Initializing chat manager...")
chat_manager = ChatManager()

print("Initializing notes manager...")
notes_manager = NotesManager()

print("Initializing session manager...")
session_manager = SessionManager()

print("Initializing agent orchestrator...")
agent_orchestrator = AgentOrchestrator(vectordb=vectordb)

print("Initializing committee flow manager...")
committee_flow_manager = CommitteeFlowManager()

# Data storage directories
DATA_DIR = os.path.join(os.path.dirname(__file__), '..', 'data')
NOTES_DIR = os.path.join(DATA_DIR, 'notes')
SPEECHES_DIR = os.path.join(DATA_DIR, 'speeches')
PREMADE_NOTES_DIR = os.path.join(DATA_DIR, 'premade_notes')

for directory in [DATA_DIR, NOTES_DIR, SPEECHES_DIR, PREMADE_NOTES_DIR]:
    os.makedirs(directory, exist_ok=True)


def get_session_id_from_request():
    """Get session ID from request header or query param"""
    return request.headers.get('X-Session-Id') or request.args.get('session_id')


def _get_notes_dir_for_request():
    """Get notes directory, session-scoped if session_id is available"""
    session_id = get_session_id_from_request()
    if session_id:
        notes_dir = session_manager.get_session_notes_dir(session_id)
        os.makedirs(str(notes_dir), exist_ok=True)
        return str(notes_dir)
    return NOTES_DIR


def _get_speeches_dir_for_request():
    """Get speeches directory, session-scoped if session_id is available"""
    session_id = get_session_id_from_request()
    if session_id:
        speeches_dir = session_manager.get_session_speeches_dir(session_id)
        os.makedirs(str(speeches_dir), exist_ok=True)
        return str(speeches_dir)
    return SPEECHES_DIR


def _get_chats_dir_for_request():
    """Get chats directory, session-scoped if session_id is available"""
    session_id = get_session_id_from_request()
    if session_id:
        chats_dir = session_manager.get_session_chats_dir(session_id)
        os.makedirs(str(chats_dir), exist_ok=True)
        return str(chats_dir)
    return os.path.join(DATA_DIR, 'chats')


# ============= SESSION ENDPOINTS =============

@app.route('/api/sessions', methods=['GET'])
def get_sessions():
    """Get all MUN sessions"""
    try:
        sessions = session_manager.get_all_sessions()
        return jsonify(sessions)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/sessions', methods=['POST'])
def create_session_endpoint():
    """Create a new MUN session"""
    try:
        data = request.json
        name = data.get('name', '')
        description = data.get('description', '')
        dates = data.get('dates', '')

        if not name:
            return jsonify({'error': 'Session name is required'}), 400

        session = session_manager.create_session(name, description, dates)
        return jsonify(session), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/sessions/<session_id>', methods=['GET'])
def get_session(session_id):
    """Get a specific session"""
    try:
        session = session_manager.get_session(session_id)
        if not session:
            return jsonify({'error': 'Session not found'}), 404
        return jsonify(session)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/sessions/<session_id>', methods=['PUT'])
def update_session_endpoint(session_id):
    """Update a session"""
    try:
        data = request.json
        name = data.get('name')
        description = data.get('description')
        dates = data.get('dates')

        session = session_manager.update_session(session_id, name, description, dates)
        if not session:
            return jsonify({'error': 'Session not found'}), 404
        return jsonify(session)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/sessions/<session_id>', methods=['DELETE'])
def delete_session_endpoint(session_id):
    """Delete a session"""
    try:
        session_manager.delete_session(session_id)
        return jsonify({'message': 'Session deleted'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/sessions/<session_id>/end', methods=['POST'])
def end_session_endpoint(session_id):
    """End a session and generate comprehensive summary"""
    try:
        # Get session data
        session = session_manager.get_session(session_id)
        if not session:
            return jsonify({'error': 'Session not found'}), 404

        # Collect all session data
        notes_dir = session_manager.get_session_notes_dir(session_id)
        speeches_dir = session_manager.get_session_speeches_dir(session_id)
        chats_dir = session_manager.get_session_chats_dir(session_id)

        # Load notes
        notes = []
        if notes_dir.exists():
            for note_file in notes_dir.glob('*.json'):
                with open(note_file, 'r') as f:
                    notes.append(json.load(f))

        # Load speeches
        speeches = []
        if speeches_dir.exists():
            for speech_file in speeches_dir.glob('*.json'):
                with open(speech_file, 'r') as f:
                    speeches.append(json.load(f))

        # Load chat history
        chat_history = []
        if chats_dir.exists():
            for chat_file in chats_dir.glob('*.json'):
                with open(chat_file, 'r') as f:
                    chat_data = json.load(f)
                    chat_history.extend(chat_data.get('messages', []))

        # Generate summary using AI
        summary_data = ai_service.generate_session_summary(
            session, notes, speeches, chat_history
        )

        # End the session with summary
        updated_session = session_manager.end_session(
            session_id,
            summary=summary_data.get('summary'),
            compressed_memory=summary_data.get('compressed_memory')
        )

        return jsonify({
            'session': updated_session,
            'summary': summary_data.get('summary'),
            'stats': summary_data.get('stats')
        })

    except Exception as e:
        print(f"Error ending session: {str(e)}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/sessions/active', methods=['GET'])
def get_active_sessions():
    """Get all active sessions"""
    try:
        sessions = session_manager.get_active_sessions()
        return jsonify(sessions)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/sessions/ended', methods=['GET'])
def get_ended_sessions():
    """Get all ended (past) sessions"""
    try:
        sessions = session_manager.get_ended_sessions()
        return jsonify(sessions)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/sessions/<session_id>/summary', methods=['GET'])
def get_session_summary(session_id):
    """Get the summary of an ended session"""
    try:
        session = session_manager.get_session(session_id)
        if not session:
            return jsonify({'error': 'Session not found'}), 404

        if not session.get('summary'):
            return jsonify({'error': 'Session has no summary. End the session first.'}), 400

        return jsonify({
            'session': session,
            'summary': session.get('summary'),
            'compressed_memory': session.get('compressed_memory')
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/sessions/<target_id>/import/<source_id>', methods=['POST'])
def import_session_memory(target_id, source_id):
    """Import compressed memory from source session to target session"""
    try:
        # Check if source session has memory
        source_session = session_manager.get_session(source_id)
        if not source_session:
            return jsonify({'error': 'Source session not found'}), 404

        if not source_session.get('compressed_memory'):
            return jsonify({'error': 'Source session has no memory to import'}), 400

        # Import memory
        updated_session = session_manager.import_memory_to_session(target_id, source_id)

        if not updated_session:
            return jsonify({'error': 'Failed to import memory'}), 500

        # If merge is needed, perform it
        if isinstance(updated_session.get('compressed_memory'), dict) and \
           updated_session['compressed_memory'].get('needs_merge'):

            merged_memory = ai_service.merge_session_memories(
                updated_session['compressed_memory']['existing'],
                updated_session['compressed_memory']['imported']
            )

            # Update with merged memory
            sessions = session_manager._load_sessions()
            for s in sessions:
                if s['id'] == target_id:
                    s['compressed_memory'] = merged_memory
                    s['updated_at'] = datetime.now().isoformat()
            session_manager._save_sessions(sessions)

            updated_session['compressed_memory'] = merged_memory

        return jsonify({
            'session': updated_session,
            'message': f'Memory imported from {source_session.get("name")}'
        })

    except Exception as e:
        print(f"Error importing memory: {str(e)}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/sessions/<session_id>/detach/<source_id>', methods=['POST'])
def detach_session_memory(session_id, source_id):
    """Remove imported memory from a session"""
    try:
        updated_session = session_manager.detach_imported_memory(session_id, source_id)

        if not updated_session:
            return jsonify({'error': 'Failed to detach memory'}), 500

        return jsonify({
            'session': updated_session,
            'message': 'Memory detached successfully'
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ============= CHAT ENDPOINTS =============

@app.route('/api/chats', methods=['GET'])
def get_chats():
    """Get all chat conversations"""
    try:
        chats = chat_manager.get_all_chats()
        return jsonify(chats)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/chats', methods=['POST'])
def create_chat():
    """Create a new chat"""
    try:
        data = request.json
        title = data.get('title', 'New Chat')
        chat = chat_manager.create_chat(title)
        return jsonify(chat), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/chats/<chat_id>', methods=['GET'])
def get_chat(chat_id):
    """Get a specific chat"""
    try:
        chat = chat_manager.load_chat(chat_id)
        if not chat:
            return jsonify({'error': 'Chat not found'}), 404
        return jsonify(chat)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/chats/<chat_id>', methods=['DELETE'])
def delete_chat(chat_id):
    """Delete a chat"""
    try:
        chat_manager.delete_chat(chat_id)
        return jsonify({'message': 'Chat deleted'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/chat', methods=['POST'])
def chat():
    """Chat endpoint with RAG and context"""
    try:
        data = request.json
        message = data.get('message', '')
        chat_id = data.get('chat_id')

        if not message:
            return jsonify({'error': 'Message is required'}), 400

        # Create new chat if none specified
        if not chat_id:
            new_chat = chat_manager.create_chat()
            chat_id = new_chat['id']

        # Get chat history
        history = chat_manager.get_chat_history_for_llm(chat_id, max_messages=10)

        # Get additional context from config and notes
        config_context = config_manager.get_context_for_llm()
        notes_context = notes_manager.get_all_notes_context()

        # Add user message to chat
        chat_manager.add_message(chat_id, 'user', message)

        # Get AI response with full context
        response = ai_service.chat_with_full_context(
            message,
            history,
            config_context,
            notes_context
        )

        # Save assistant response
        chat_manager.add_message(chat_id, 'assistant', response)

        return jsonify({
            'response': response,
            'chat_id': chat_id,
            'timestamp': datetime.now().isoformat()
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/speech/generate', methods=['POST'])
def generate_speech():
    """Generate MUN speech with notes context"""
    try:
        data = request.json
        country = data.get('country', '')
        topic = data.get('topic', '')
        committee = data.get('committee', '')
        stance = data.get('stance', '')
        speech_type = data.get('speech_type', 'GSL')

        if not country or not topic:
            return jsonify({'error': 'Country and topic are required'}), 400

        # Get notes context for speech generation
        notes_context = notes_manager.get_all_notes_context()

        speech = ai_service.generate_speech(
            country, topic, committee, stance, speech_type, notes_context
        )

        # Save speech
        speech_id = f"speech_{uuid.uuid4().hex[:12]}"
        speech_data = {
            'id': speech_id,
            'country': country,
            'topic': topic,
            'committee': committee,
            'stance': stance,
            'speech_type': speech_type,
            'content': speech,
            'created_at': datetime.now().isoformat()
        }

        speech_file = os.path.join(SPEECHES_DIR, f"{speech_id}.json")
        with open(speech_file, 'w') as f:
            json.dump(speech_data, f, indent=2)

        return jsonify(speech_data)

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/speeches', methods=['GET'])
def get_speeches():
    """Get all saved speeches"""
    try:
        speeches = []
        for filename in os.listdir(SPEECHES_DIR):
            if filename.endswith('.json'):
                with open(os.path.join(SPEECHES_DIR, filename), 'r') as f:
                    speeches.append(json.load(f))

        speeches.sort(key=lambda x: x.get('created_at', ''), reverse=True)
        return jsonify(speeches)

    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ============= NOTES ENDPOINTS =============

@app.route('/api/notes', methods=['GET', 'POST'])
def notes():
    """Get all notes or create a new note"""
    if request.method == 'GET':
        try:
            notes = []
            for filename in os.listdir(NOTES_DIR):
                if filename.endswith('.json'):
                    with open(os.path.join(NOTES_DIR, filename), 'r') as f:
                        notes.append(json.load(f))

            notes.sort(key=lambda x: x.get('updated_at', ''), reverse=True)
            return jsonify(notes)

        except Exception as e:
            return jsonify({'error': str(e)}), 500

    elif request.method == 'POST':
        try:
            data = request.json
            title = data.get('title', 'Untitled Note')
            content = data.get('content', '')

            note_id = f"note_{uuid.uuid4().hex[:12]}"
            note_data = {
                'id': note_id,
                'title': title,
                'content': content,
                'created_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat(),
                'analysis': None
            }

            notes_dir = _get_notes_dir_for_request()
            note_file = os.path.join(notes_dir, f"{note_id}.json")
            with open(note_file, 'w') as f:
                json.dump(note_data, f, indent=2)

            return jsonify(note_data), 201

        except Exception as e:
            return jsonify({'error': str(e)}), 500


@app.route('/api/notes/<note_id>', methods=['GET', 'PUT', 'DELETE'])
def note_detail(note_id):
    """Get, update, or delete a specific note"""
    note_file = os.path.join(NOTES_DIR, f"{note_id}.json")

    if request.method == 'GET':
        try:
            if not os.path.exists(note_file):
                return jsonify({'error': 'Note not found'}), 404

            with open(note_file, 'r') as f:
                return jsonify(json.load(f))

        except Exception as e:
            return jsonify({'error': str(e)}), 500

    elif request.method == 'PUT':
        try:
            if not os.path.exists(note_file):
                return jsonify({'error': 'Note not found'}), 404

            with open(note_file, 'r') as f:
                note_data = json.load(f)

            data = request.json
            note_data['title'] = data.get('title', note_data['title'])
            note_data['content'] = data.get('content', note_data['content'])
            note_data['updated_at'] = datetime.now().isoformat()

            with open(note_file, 'w') as f:
                json.dump(note_data, f, indent=2)

            return jsonify(note_data)

        except Exception as e:
            return jsonify({'error': str(e)}), 500

    elif request.method == 'DELETE':
        try:
            if not os.path.exists(note_file):
                return jsonify({'error': 'Note not found'}), 404

            os.remove(note_file)
            return jsonify({'message': 'Note deleted successfully'})

        except Exception as e:
            return jsonify({'error': str(e)}), 500


@app.route('/api/notes/<note_id>/analyze', methods=['POST'])
def analyze_note(note_id):
    """Analyze a note and generate insights"""
    try:
        note_file = os.path.join(NOTES_DIR, f"{note_id}.json")
        if not os.path.exists(note_file):
            return jsonify({'error': 'Note not found'}), 404

        with open(note_file, 'r') as f:
            note_data = json.load(f)

        # Analyze the note
        analysis = ai_service.analyze_notes(note_data['content'])

        # Save analysis
        note_data['analysis'] = analysis
        note_data['analyzed_at'] = datetime.now().isoformat()

        with open(note_file, 'w') as f:
            json.dump(note_data, f, indent=2)

        return jsonify(analysis)

    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ============= RESEARCH TOOLS ENDPOINTS =============

@app.route('/api/research/poi', methods=['POST'])
def generate_poi():
    """Generate POI questions using agentic workflow"""
    try:
        data = request.json
        country = data.get('country', '')
        topic = data.get('topic', '')
        target_country = data.get('target_country', '')

        if not country or not topic:
            return jsonify({'error': 'Country and topic are required'}), 400

        # Use agent orchestrator for professional output
        result = agent_orchestrator.generate_poi_questions(country, topic, target_country)

        # Parse output into questions list for compatibility
        output_lines = result['output'].split('\n')
        questions = [line.strip() for line in output_lines if line.strip() and (line.strip().startswith('1.') or line.strip().startswith('**'))]

        return jsonify({
            'questions': questions,
            'formatted_output': result['output'],  # Full markdown output
            'country': country,
            'topic': topic,
            'target_country': target_country
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/research/foreign-policy', methods=['POST'])
def research_foreign_policy():
    """Research foreign policy using agentic workflow"""
    try:
        data = request.json
        country = data.get('country', '')
        topic = data.get('topic', '')

        if not country or not topic:
            return jsonify({'error': 'Country and topic are required'}), 400

        # Use agent orchestrator
        result = agent_orchestrator.research_foreign_policy(country, topic)

        return jsonify({
            'policy': result['output'],
            'country': country,
            'topic': topic
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/research/modcaucus', methods=['POST'])
def suggest_modcaucus():
    """Suggest moderated caucus topics using agentic workflow"""
    try:
        data = request.json
        agenda = data.get('agenda', '')
        committee = data.get('committee', '')

        if not agenda:
            return jsonify({'error': 'Agenda is required'}), 400

        # Use agent orchestrator
        result = agent_orchestrator.suggest_modcaucus_topics(agenda, committee)

        # Extract topics list for compatibility
        output_lines = result['output'].split('\n')
        topics = [line.strip() for line in output_lines if line.strip() and (line.strip()[0].isdigit() or line.strip().startswith('**'))]

        return jsonify({
            'topics': topics,
            'formatted_output': result['output'],
            'agenda': agenda,
            'committee': committee
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ============= PREMADE NOTES ENDPOINTS =============

@app.route('/api/premade-notes', methods=['GET'])
def get_premade_notes():
    """Get all premade notes"""
    try:
        notes = []
        for filename in os.listdir(PREMADE_NOTES_DIR):
            if filename.endswith('.json'):
                with open(os.path.join(PREMADE_NOTES_DIR, filename), 'r') as f:
                    notes.append(json.load(f))

        return jsonify(notes)

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/premade-notes/<section>', methods=['GET'])
def get_premade_note(section):
    """Get a specific premade note"""
    try:
        note_file = os.path.join(PREMADE_NOTES_DIR, f"{section}.json")
        if not os.path.exists(note_file):
            return jsonify({'error': 'Note not found'}), 404

        with open(note_file, 'r') as f:
            return jsonify(json.load(f))

    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ============= VECTOR DB SEARCH ENDPOINT =============

@app.route('/api/search', methods=['POST'])
def search_book():
    """Search the MUN book"""
    try:
        data = request.json
        query = data.get('query', '')

        if not query:
            return jsonify({'error': 'Query is required'}), 400

        results = vectordb.search(query, n_results=5)

        return jsonify({
            'results': results,
            'query': query
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ============= FRONTEND ROUTES =============

@app.route('/')
def serve_frontend():
    """Serve the main frontend page"""
    return send_from_directory(app.static_folder, 'index.html')


@app.route('/<path:path>')
def serve_static(path):
    """Serve static files"""
    return send_from_directory(app.static_folder, path)


# ============= CONFIGURATION ENDPOINTS =============

@app.route('/api/config', methods=['GET'])
def get_config():
    """Get configuration"""
    try:
        return jsonify(config_manager.config)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/config/delegate', methods=['POST'])
def update_delegate():
    """Update my delegate information"""
    try:
        data = request.json
        config_manager.update_my_delegate(
            data.get('country', ''),
            data.get('committee', ''),
            data.get('agenda', ''),
            data.get('portfolio', '')
        )
        return jsonify(config_manager.config)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/config/delegates', methods=['POST'])
def add_delegate():
    """Add another delegate"""
    try:
        data = request.json
        delegate = config_manager.add_other_delegate(
            data.get('country', ''),
            data.get('notes', '')
        )
        return jsonify(delegate), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/config/delegates/<delegate_id>', methods=['DELETE'])
def remove_delegate(delegate_id):
    """Remove a delegate"""
    try:
        config_manager.remove_delegate(delegate_id)
        return jsonify({'message': 'Delegate removed'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/config/committee', methods=['POST'])
def update_committee():
    """Update committee information"""
    try:
        data = request.json
        config_manager.update_committee_info(
            data.get('committee', ''),
            data.get('agenda', ''),
            data.get('study_guide', ''),
            data.get('position_paper_due', '')
        )
        return jsonify(config_manager.config)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ============= ENHANCED NOTES ENDPOINTS =============

@app.route('/api/notes-v2/folders', methods=['GET'])
def get_folders():
    """Get folder structure"""
    try:
        return jsonify(notes_manager.folders)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/notes-v2/folders', methods=['POST'])
def create_folder():
    """Create a new folder"""
    try:
        data = request.json
        folder = notes_manager.create_folder(
            data.get('name', 'New Folder'),
            data.get('icon', '📁')
        )
        return jsonify(folder), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/notes-v2/templates', methods=['GET'])
def get_templates():
    """Get note templates"""
    try:
        return jsonify(notes_manager.get_templates())
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/notes-v2/from-template', methods=['POST'])
def create_note_from_template():
    """Create note from template"""
    try:
        data = request.json
        note = notes_manager.create_note_from_template(
            data.get('template_id'),
            data.get('title')
        )
        if not note:
            return jsonify({'error': 'Template not found'}), 404
        return jsonify(note), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/notes/<note_id>/move-to-folder', methods=['POST'])
def move_note_to_folder(note_id):
    """Move a note to a folder"""
    try:
        note_file = os.path.join(NOTES_DIR, f"{note_id}.json")
        if not os.path.exists(note_file):
            return jsonify({'error': 'Note not found'}), 404

        with open(note_file, 'r') as f:
            note_data = json.load(f)

        data = request.json
        folder_id = data.get('folder_id')

        note_data['folder'] = folder_id
        note_data['updated_at'] = datetime.now().isoformat()

        with open(note_file, 'w') as f:
            json.dump(note_data, f, indent=2)

        return jsonify(note_data)

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/research/comprehensive', methods=['POST'])
def comprehensive_research():
    """Do comprehensive research on everything and automatically save as notes"""
    try:
        data = request.json
        country = data.get('country', '')
        topic = data.get('topic', '')
        committee = data.get('committee', '')

        if not country or not topic:
            return jsonify({'error': 'Country and topic are required'}), 400

        # Generate comprehensive research
        print(f"Generating comprehensive research for {country} on {topic}...")

        allies_research = ai_service.suggest_allies(country, topic)
        opposition_research = ai_service.identify_opposition(country, topic)
        key_facts = ai_service.get_key_facts(country, topic)
        resolution_ideas = ai_service.generate_resolution_ideas(country, topic, committee)

        # Automatically create notes for each research type
        notes_created = []
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

        # Note 1: Allies & Lobbying Strategy
        note1_id = f"note_{timestamp}_allies"
        note1 = {
            'id': note1_id,
            'title': f'Allies & Lobbying Strategy - {topic}',
            'content': allies_research,
            'folder': 'lobbying',
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat(),
            'analysis': None
        }
        note1_file = os.path.join(NOTES_DIR, f"{note1_id}.json")
        with open(note1_file, 'w') as f:
            json.dump(note1, f, indent=2)
        notes_created.append(note1)

        # Note 2: Opposition Analysis
        import time
        time.sleep(0.1)  # Ensure unique IDs
        note2_id = f"note_{datetime.now().strftime('%Y%m%d_%H%M%S')}_opposition"
        note2 = {
            'id': note2_id,
            'title': f'Opposition Analysis - {topic}',
            'content': opposition_research,
            'folder': 'research',
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat(),
            'analysis': None
        }
        note2_file = os.path.join(NOTES_DIR, f"{note2_id}.json")
        with open(note2_file, 'w') as f:
            json.dump(note2, f, indent=2)
        notes_created.append(note2)

        # Note 3: Key Facts & Statistics
        time.sleep(0.1)
        note3_id = f"note_{datetime.now().strftime('%Y%m%d_%H%M%S')}_facts"
        note3 = {
            'id': note3_id,
            'title': f'Key Facts & Statistics - {country} on {topic}',
            'content': key_facts,
            'folder': 'research',
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat(),
            'analysis': None
        }
        note3_file = os.path.join(NOTES_DIR, f"{note3_id}.json")
        with open(note3_file, 'w') as f:
            json.dump(note3, f, indent=2)
        notes_created.append(note3)

        # Note 4: Resolution Strategy
        time.sleep(0.1)
        note4_id = f"note_{datetime.now().strftime('%Y%m%d_%H%M%S')}_resolution"
        note4 = {
            'id': note4_id,
            'title': f'Resolution Strategy - {topic}',
            'content': resolution_ideas,
            'folder': 'documentation',
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat(),
            'analysis': None
        }
        note4_file = os.path.join(NOTES_DIR, f"{note4_id}.json")
        with open(note4_file, 'w') as f:
            json.dump(note4, f, indent=2)
        notes_created.append(note4)

        print(f"Created {len(notes_created)} notes from comprehensive research")

        return jsonify({
            'success': True,
            'message': f'Created {len(notes_created)} detailed research notes!',
            'notes_created': notes_created,
            'summary': {
                'allies': allies_research[:300] + '...',
                'opposition': opposition_research[:300] + '...',
                'key_facts': key_facts[:300] + '...',
                'resolution': resolution_ideas[:300] + '...'
            }
        })

    except Exception as e:
        print(f"Error in comprehensive research: {str(e)}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/research/country-profile', methods=['POST'])
def country_profile():
    """Get comprehensive country profile using agentic workflow"""
    try:
        data = request.json
        country = data.get('country', '')
        topic = data.get('topic', '')

        if not country:
            return jsonify({'error': 'Country is required'}), 400

        # Use agent orchestrator
        result = agent_orchestrator.generate_country_profile(country, topic)
        return jsonify({'profile': result['output'], 'country': country})

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/research/resolution-builder', methods=['POST'])
def resolution_builder():
    """Build resolution clauses"""
    try:
        data = request.json
        country = data.get('country', '')
        topic = data.get('topic', '')
        committee = data.get('committee', '')

        if not topic:
            return jsonify({'error': 'Topic is required'}), 400

        resolution = ai_service.generate_resolution_draft(country, topic, committee)
        return jsonify({'resolution': resolution})

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/research/crisis-response', methods=['POST'])
def crisis_response():
    """Generate crisis response using agentic workflow"""
    try:
        data = request.json
        country = data.get('country', '')
        crisis = data.get('crisis', '')

        if not country or not crisis:
            return jsonify({'error': 'Country and crisis are required'}), 400

        # Use agent orchestrator
        result = agent_orchestrator.generate_crisis_response(country, crisis)
        return jsonify({'response': result['output']})

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/research/debate-prep', methods=['POST'])
def debate_prep():
    """Prepare for debate against specific country using agentic workflow"""
    try:
        data = request.json
        my_country = data.get('my_country', '')
        opponent_country = data.get('opponent_country', '')
        topic = data.get('topic', '')

        if not my_country or not opponent_country or not topic:
            return jsonify({'error': 'All fields are required'}), 400

        # Use agent orchestrator
        result = agent_orchestrator.prepare_debate(my_country, opponent_country, topic)
        return jsonify({'preparation': result['output']})

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/research/allies', methods=['POST'])
def get_allies():
    """Get potential allies using agentic workflow"""
    try:
        data = request.json
        country = data.get('country', '')
        topic = data.get('topic', '')

        if not country or not topic:
            return jsonify({'error': 'Country and topic are required'}), 400

        # Use agent orchestrator
        result = agent_orchestrator.find_allies(country, topic)
        return jsonify({'allies': result['output']})

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/research/opposition', methods=['POST'])
def get_opposition():
    """Get potential opposition using agentic workflow"""
    try:
        data = request.json
        country = data.get('country', '')
        topic = data.get('topic', '')

        if not country or not topic:
            return jsonify({'error': 'Country and topic are required'}), 400

        # Use agent orchestrator
        result = agent_orchestrator.analyze_opposition(country, topic)
        return jsonify({'opposition': result['output']})

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/notes/save-research', methods=['POST'])
def save_research_to_notes():
    """Save research results to notes"""
    try:
        data = request.json
        title = data.get('title', 'Research Note')
        content = data.get('content', '')
        folder = data.get('folder', 'research')

        note_id = f"note_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        note_data = {
            'id': note_id,
            'title': title,
            'content': content,
            'folder': folder,
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat(),
            'analysis': None
        }

        note_file = os.path.join(NOTES_DIR, f"{note_id}.json")
        with open(note_file, 'w') as f:
            json.dump(note_data, f, indent=2)

        # Track in memory
        agent_orchestrator.memory.track_note_created(
            note_id,
            title,
            folder,
            content[:200]
        )

        return jsonify(note_data), 201

    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ============= STREAMING ENDPOINTS (Server-Sent Events) =============

@app.route('/api/research/comprehensive-stream', methods=['POST'])
def comprehensive_research_stream():
    """Stream comprehensive research pipeline with real-time updates"""
    try:
        data = request.json
        country = data.get('country', '')
        topic = data.get('topic', '')
        committee = data.get('committee', '')

        if not country or not topic:
            return jsonify({'error': 'Country and topic are required'}), 400

        def generate():
            """Generator for Server-Sent Events"""
            try:
                # Execute the comprehensive pipeline with streaming
                for update in agent_orchestrator.execute_comprehensive_research_pipeline(
                    country, topic, committee, stream=True
                ):
                    # Format as SSE event
                    yield f"data: {json.dumps(update)}\n\n"

            except Exception as e:
                yield f"data: {json.dumps({'error': str(e), 'stage': 'error'})}\n\n"

        return app.response_class(
            generate(),
            mimetype='text/event-stream',
            headers={
                'Cache-Control': 'no-cache',
                'X-Accel-Buffering': 'no',
                'Connection': 'keep-alive'
            }
        )

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/research/crisis-stream', methods=['POST'])
def crisis_response_stream():
    """Stream crisis response pipeline"""
    try:
        data = request.json
        country = data.get('country', '')
        crisis = data.get('crisis', '')

        if not country or not crisis:
            return jsonify({'error': 'Country and crisis description are required'}), 400

        def generate():
            """Generator for Server-Sent Events"""
            try:
                for update in agent_orchestrator.execute_crisis_pipeline(
                    country, crisis, stream=True
                ):
                    yield f"data: {json.dumps(update)}\n\n"

            except Exception as e:
                yield f"data: {json.dumps({'error': str(e), 'stage': 'error'})}\n\n"

        return app.response_class(
            generate(),
            mimetype='text/event-stream',
            headers={
                'Cache-Control': 'no-cache',
                'X-Accel-Buffering': 'no'
            }
        )

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/research/debate-mastery-stream', methods=['POST'])
def debate_mastery_stream():
    """Stream debate preparation pipeline"""
    try:
        data = request.json
        country = data.get('country', '')
        topic = data.get('topic', '')
        opponent = data.get('opponent_country', '')

        if not country or not topic:
            return jsonify({'error': 'Country and topic are required'}), 400

        def generate():
            """Generator for Server-Sent Events"""
            try:
                for update in agent_orchestrator.execute_debate_mastery_pipeline(
                    country, topic, opponent, stream=True
                ):
                    yield f"data: {json.dumps(update)}\n\n"

            except Exception as e:
                yield f"data: {json.dumps({'error': str(e), 'stage': 'error'})}\n\n"

        return app.response_class(
            generate(),
            mimetype='text/event-stream',
            headers={
                'Cache-Control': 'no-cache',
                'X-Accel-Buffering': 'no'
            }
        )

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/research/parallel', methods=['POST'])
def parallel_research():
    """Execute multiple research tasks in parallel"""
    try:
        data = request.json
        country = data.get('country', '')
        topic = data.get('topic', '')
        tasks = data.get('tasks', ['research', 'allies', 'opposition'])

        if not country or not topic:
            return jsonify({'error': 'Country and topic are required'}), 400

        # Execute parallel pipeline
        result = agent_orchestrator.execute_parallel_pipeline(country, topic, tasks)

        return jsonify(result)

    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ============= LIVE AUTO-NOTES =============

@app.route('/api/live-auto-notes/process-stream', methods=['POST'])
def process_live_notes_stream():
    """
    Process live transcript chunks and stream important notes in real-time.
    Optimized for <500ms latency using Gemma agents.
    """
    try:
        data = request.json
        transcript_chunk = data.get('transcript_chunk', '')
        speaker = data.get('speaker', 'Unknown')
        timestamp = data.get('timestamp', '')

        if not transcript_chunk:
            return jsonify({'error': 'transcript_chunk is required'}), 400

        # Get session context if available
        session_id = data.get('session_id', '')
        context = None
        if session_id:
            try:
                session_info = session_manager.get_session(session_id)
                context = f"Delegate: {session_info.get('delegate_name', '')}, Country: {session_info.get('country', '')}, Topic: {session_info.get('topic', '')}"
            except:
                pass

        def generate():
            """Generator for Server-Sent Events"""
            try:
                # Execute the live notes pipeline with streaming
                for update in agent_orchestrator.execute_live_notes_pipeline(
                    transcript_chunk=transcript_chunk,
                    speaker=speaker,
                    timestamp=timestamp,
                    context=context,
                    stream=True
                ):
                    # Format as SSE event
                    yield f"data: {json.dumps(update)}\n\n"

            except Exception as e:
                yield f"data: {json.dumps({'error': str(e), 'stage': 'error'})}\n\n"

        return app.response_class(
            generate(),
            mimetype='text/event-stream',
            headers={
                'Cache-Control': 'no-cache',
                'X-Accel-Buffering': 'no',
                'Connection': 'keep-alive'
            }
        )

    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ============= SPEECH TRANSCRIPTION =============

@app.route('/api/transcribe', methods=['POST'])
def transcribe_speech():
    """
    Transcribe audio using OpenAI Whisper API
    Accepts audio file upload
    """
    try:
        if 'audio' not in request.files:
            return jsonify({'error': 'No audio file provided'}), 400

        audio_file = request.files['audio']

        # Check if OpenAI is available
        if not hasattr(ai_service, 'openai_client') or ai_service.openai_client is None:
            return jsonify({'error': 'OpenAI API not configured. Using browser speech recognition instead.'}), 503

        # Transcribe using Whisper
        import tempfile
        import os

        # Save temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as temp_file:
            audio_file.save(temp_file.name)
            temp_path = temp_file.name

        try:
            # Transcribe using OpenAI Whisper
            with open(temp_path, 'rb') as audio:
                transcript = ai_service.openai_client.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio,
                    language="en"
                )

            os.unlink(temp_path)  # Clean up

            return jsonify({
                'transcription': transcript.text,
                'timestamp': datetime.now().isoformat()
            })

        except Exception as e:
            if os.path.exists(temp_path):
                os.unlink(temp_path)
            raise e

    except Exception as e:
        print(f"Transcription error: {e}")
        return jsonify({'error': str(e)}), 500


# ============= SPEECH RATING & ANALYSIS =============

@app.route('/api/speech/rate-grammar', methods=['POST'])
def rate_speech_grammar():
    """Analyze speech grammar and language quality"""
    try:
        data = request.json
        speech_text = data.get('speech_text', '')

        if not speech_text:
            return jsonify({'error': 'Speech text is required'}), 400

        result = ai_service.analyze_speech_grammar(speech_text)
        return jsonify(result)

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/speech/rate-ethics', methods=['POST'])
def rate_speech_ethics():
    """Evaluate speech ethics and diplomatic appropriateness"""
    try:
        data = request.json
        speech_text = data.get('speech_text', '')
        country = data.get('country', '')

        if not speech_text:
            return jsonify({'error': 'Speech text is required'}), 400

        result = ai_service.analyze_speech_ethics(speech_text, country)
        return jsonify(result)

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/speech/rate-impact', methods=['POST'])
def rate_speech_impact():
    """Analyze speech impact and persuasiveness"""
    try:
        data = request.json
        speech_text = data.get('speech_text', '')
        topic = data.get('topic', '')
        committee = data.get('committee', '')

        if not speech_text:
            return jsonify({'error': 'Speech text is required'}), 400

        result = ai_service.analyze_speech_impact(speech_text, topic, committee)
        return jsonify(result)

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/speech/rate-comprehensive', methods=['POST'])
def rate_speech_comprehensive():
    """Comprehensive speech rating across all dimensions"""
    try:
        data = request.json
        speech_text = data.get('speech_text', '')
        country = data.get('country', '')
        topic = data.get('topic', '')
        committee = data.get('committee', '')

        if not speech_text:
            return jsonify({'error': 'Speech text is required'}), 400

        result = ai_service.rate_speech_comprehensive(speech_text, country, topic, committee)
        return jsonify(result)

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/speech/summary-and-rewrite', methods=['POST'])
def generate_summary_and_rewrite():
    """Generate comprehensive summary and improved speech rewrite"""
    try:
        data = request.json
        speech_text = data.get('speech_text', '')
        grammar_analysis = data.get('grammar_analysis', '')
        ethics_analysis = data.get('ethics_analysis', '')
        impact_analysis = data.get('impact_analysis', '')
        country = data.get('country', '')
        topic = data.get('topic', '')

        if not speech_text:
            return jsonify({'error': 'Speech text is required'}), 400

        result = ai_service.generate_speech_summary_and_rewrite(
            speech_text, grammar_analysis, ethics_analysis, impact_analysis, country, topic
        )
        return jsonify(result)

    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ============= CHIT GENERATOR =============

@app.route('/api/chit/poi', methods=['POST'])
def generate_poi_chit():
    """Generate a POI chit"""
    try:
        data = request.json
        to_country = data.get('to_country', '')
        question = data.get('question', '')
        topic = data.get('topic', '')
        my_country = data.get('my_country', '')

        if not to_country:
            return jsonify({'error': 'Target country is required'}), 400

        result = ai_service.generate_poi_chit(to_country, question, topic, my_country)
        return jsonify({'chit': result})

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/chit/lobby', methods=['POST'])
def generate_lobbying_chit():
    """Generate a lobbying chit"""
    try:
        data = request.json
        to_country = data.get('to_country', '')
        purpose = data.get('purpose', '')
        my_country = data.get('my_country', '')
        topic = data.get('topic', '')

        if not to_country:
            return jsonify({'error': 'Target country is required'}), 400

        result = ai_service.generate_lobbying_chit(to_country, purpose, my_country, topic)
        return jsonify({'chit': result})

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/chit/general', methods=['POST'])
def generate_general_chit():
    """Generate a general communication chit"""
    try:
        data = request.json
        to_country = data.get('to_country', '')
        message = data.get('message', '')
        my_country = data.get('my_country', '')
        tone = data.get('tone', 'professional')

        if not to_country or not message:
            return jsonify({'error': 'Target country and message are required'}), 400

        result = ai_service.generate_general_chit(to_country, message, my_country, tone)
        return jsonify({'chit': result})

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/chit/directive', methods=['POST'])
def generate_directive_chit():
    """Generate a directive chit"""
    try:
        data = request.json
        to_country = data.get('to_country', '')
        directive = data.get('directive', '')
        my_country = data.get('my_country', '')
        urgency = data.get('urgency', 'normal')

        if not to_country or not directive:
            return jsonify({'error': 'Target country and directive are required'}), 400

        result = ai_service.generate_directive_chit(to_country, directive, my_country, urgency)
        return jsonify({'chit': result})

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/chit/respond', methods=['POST'])
def generate_chit_response():
    """Generate a response to a received chit"""
    try:
        data = request.json
        original_chit = data.get('original_chit', '')
        response_type = data.get('response_type', 'positive')
        my_country = data.get('my_country', '')

        if not original_chit:
            return jsonify({'error': 'Original chit text is required'}), 400

        result = ai_service.generate_chit_response(original_chit, response_type, my_country)
        return jsonify({'chit': result})

    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ============= NOTES EXPORT =============

@app.route('/api/notes/<note_id>/export/txt', methods=['GET'])
def export_note_txt(note_id):
    """Export a note as TXT file"""
    try:
        session_id = get_session_id_from_request()
        if not session_id:
            return jsonify({'error': 'No active session'}), 400

        notes_dir = session_manager.get_session_notes_dir(session_id)
        note_file = notes_dir / f'{note_id}.json'

        if not note_file.exists():
            return jsonify({'error': 'Note not found'}), 404

        with open(note_file, 'r') as f:
            note = json.load(f)

        # Format as plain text
        txt_content = f"{note['title']}\n"
        txt_content += "=" * len(note['title']) + "\n\n"

        if note.get('folder'):
            txt_content += f"Folder: {note['folder']}\n"

        txt_content += f"Created: {note.get('created_at', 'Unknown')}\n"
        txt_content += f"Updated: {note.get('updated_at', 'Unknown')}\n\n"
        txt_content += "-" * 50 + "\n\n"
        txt_content += note['content']

        # Create BytesIO object
        buffer = BytesIO()
        buffer.write(txt_content.encode('utf-8'))
        buffer.seek(0)

        filename = f"{note['title'].replace(' ', '_')}.txt"

        return send_file(
            buffer,
            mimetype='text/plain',
            as_attachment=True,
            download_name=filename
        )

    except Exception as e:
        print(f"Error exporting note as TXT: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/notes/<note_id>/export/pdf', methods=['GET'])
def export_note_pdf(note_id):
    """Export a note as PDF file"""
    try:
        session_id = get_session_id_from_request()
        if not session_id:
            return jsonify({'error': 'No active session'}), 400

        notes_dir = session_manager.get_session_notes_dir(session_id)
        note_file = notes_dir / f'{note_id}.json'

        if not note_file.exists():
            return jsonify({'error': 'Note not found'}), 404

        with open(note_file, 'r') as f:
            note = json.load(f)

        # Try to use reportlab for PDF generation
        try:
            from reportlab.lib.pagesizes import letter
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
            from reportlab.lib.units import inch
            from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
            from reportlab.lib.enums import TA_CENTER

            buffer = BytesIO()

            # Create PDF
            doc = SimpleDocTemplate(buffer, pagesize=letter,
                                   rightMargin=72, leftMargin=72,
                                   topMargin=72, bottomMargin=18)

            # Container for the 'Flowable' objects
            elements = []

            # Define styles
            styles = getSampleStyleSheet()
            styles.add(ParagraphStyle(name='CustomTitle',
                                     parent=styles['Heading1'],
                                     fontSize=24,
                                     textColor='#2563eb',
                                     spaceAfter=30,
                                     alignment=TA_CENTER))

            styles.add(ParagraphStyle(name='CustomBody',
                                     parent=styles['BodyText'],
                                     fontSize=11,
                                     leading=16,
                                     spaceAfter=12))

            # Add title
            title = Paragraph(note['title'], styles['CustomTitle'])
            elements.append(title)
            elements.append(Spacer(1, 12))

            # Add metadata
            metadata_style = styles['Normal']
            if note.get('folder'):
                folder_para = Paragraph(f"<b>Folder:</b> {note['folder']}", metadata_style)
                elements.append(folder_para)

            created = Paragraph(f"<b>Created:</b> {note.get('created_at', 'Unknown')}", metadata_style)
            elements.append(created)

            updated = Paragraph(f"<b>Updated:</b> {note.get('updated_at', 'Unknown')}", metadata_style)
            elements.append(updated)

            elements.append(Spacer(1, 20))

            # Add content - convert markdown to HTML first
            html_content = markdown2.markdown(note['content'])

            # Split content into paragraphs and add to PDF
            for line in html_content.split('\n'):
                if line.strip():
                    # Clean HTML tags for reportlab
                    cleaned_line = line.replace('<p>', '').replace('</p>', '')
                    cleaned_line = cleaned_line.replace('<strong>', '<b>').replace('</strong>', '</b>')
                    cleaned_line = cleaned_line.replace('<em>', '<i>').replace('</em>', '</i>')

                    para = Paragraph(cleaned_line, styles['CustomBody'])
                    elements.append(para)

            # Build PDF
            doc.build(elements)

            buffer.seek(0)
            filename = f"{note['title'].replace(' ', '_')}.pdf"

            return send_file(
                buffer,
                mimetype='application/pdf',
                as_attachment=True,
                download_name=filename
            )

        except ImportError:
            # Fallback if reportlab is not installed
            return jsonify({
                'error': 'PDF export requires reportlab library. Install with: pip install reportlab'
            }), 500

    except Exception as e:
        print(f"Error exporting note as PDF: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/notes/export-all/txt', methods=['GET'])
def export_all_notes_txt():
    """Export all notes from current session as a single TXT file"""
    try:
        session_id = get_session_id_from_request()
        if not session_id:
            return jsonify({'error': 'No active session'}), 400

        session = session_manager.get_session(session_id)
        notes_dir = session_manager.get_session_notes_dir(session_id)

        if not notes_dir.exists():
            return jsonify({'error': 'No notes found'}), 404

        # Collect all notes
        all_notes = []
        for note_file in notes_dir.glob('*.json'):
            with open(note_file, 'r') as f:
                all_notes.append(json.load(f))

        # Sort by created date
        all_notes.sort(key=lambda x: x.get('created_at', ''))

        # Format as plain text
        txt_content = f"{session['name']} - All Notes\n"
        txt_content += "=" * 50 + "\n\n"
        txt_content += f"Exported: {datetime.now().isoformat()}\n"
        txt_content += f"Total Notes: {len(all_notes)}\n\n"
        txt_content += "=" * 50 + "\n\n"

        for i, note in enumerate(all_notes, 1):
            txt_content += f"\n\n{'=' * 50}\n"
            txt_content += f"Note {i}: {note['title']}\n"
            txt_content += f"{'=' * 50}\n\n"

            if note.get('folder'):
                txt_content += f"Folder: {note['folder']}\n"
            txt_content += f"Created: {note.get('created_at', 'Unknown')}\n\n"
            txt_content += note['content']
            txt_content += f"\n\n{'-' * 50}\n"

        # Create BytesIO object
        buffer = BytesIO()
        buffer.write(txt_content.encode('utf-8'))
        buffer.seek(0)

        filename = f"{session['name'].replace(' ', '_')}_all_notes.txt"

        return send_file(
            buffer,
            mimetype='text/plain',
            as_attachment=True,
            download_name=filename
        )

    except Exception as e:
        print(f"Error exporting all notes: {e}")
        return jsonify({'error': str(e)}), 500


# ============= COMMITTEE FLOW ENDPOINTS =============

@app.route('/api/committee-flow/templates', methods=['GET'])
def get_flow_templates():
    """Get available building block templates"""
    try:
        templates = committee_flow_manager.get_block_templates()
        return jsonify(templates)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/committee-flow', methods=['GET', 'POST'])
def committee_flows():
    """Get all flows or create a new flow"""
    if request.method == 'GET':
        try:
            session_id = request.args.get('session_id')
            flows = committee_flow_manager.get_all_flows(session_id)
            return jsonify(flows)
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    elif request.method == 'POST':
        try:
            data = request.json
            name = data.get('name', 'New Committee Flow')
            session_id = data.get('session_id')

            flow = committee_flow_manager.create_flow(name, session_id)
            return jsonify(flow), 201
        except Exception as e:
            return jsonify({'error': str(e)}), 500


@app.route('/api/committee-flow/<flow_id>', methods=['GET', 'PUT', 'DELETE'])
def committee_flow_detail(flow_id):
    """Get, update, or delete a specific flow"""
    if request.method == 'GET':
        try:
            flow = committee_flow_manager.get_flow(flow_id)
            if not flow:
                return jsonify({'error': 'Flow not found'}), 404
            return jsonify(flow)
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    elif request.method == 'PUT':
        try:
            data = request.json
            flow = committee_flow_manager.update_flow(flow_id, **data)
            if not flow:
                return jsonify({'error': 'Flow not found'}), 404
            return jsonify(flow)
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    elif request.method == 'DELETE':
        try:
            committee_flow_manager.delete_flow(flow_id)
            return jsonify({'message': 'Flow deleted successfully'})
        except Exception as e:
            return jsonify({'error': str(e)}), 500


@app.route('/api/committee-flow/<flow_id>/blocks', methods=['POST'])
def add_block_to_flow(flow_id):
    """Add a building block to the flow"""
    try:
        data = request.json
        block_type = data.get('type')
        block_data = data.get('data', {})

        if not block_type:
            return jsonify({'error': 'Block type is required'}), 400

        block = committee_flow_manager.add_block(flow_id, block_type, block_data)
        if not block:
            return jsonify({'error': 'Flow not found'}), 404

        return jsonify(block), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/committee-flow/<flow_id>/blocks/<block_id>', methods=['PUT', 'DELETE'])
def manage_block(flow_id, block_id):
    """Update or delete a specific block"""
    if request.method == 'PUT':
        try:
            data = request.json
            block = committee_flow_manager.update_block(flow_id, block_id, **data)
            if not block:
                return jsonify({'error': 'Block not found'}), 404
            return jsonify(block)
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    elif request.method == 'DELETE':
        try:
            success = committee_flow_manager.delete_block(flow_id, block_id)
            if not success:
                return jsonify({'error': 'Block not found'}), 404
            return jsonify({'message': 'Block deleted successfully'})
        except Exception as e:
            return jsonify({'error': str(e)}), 500


@app.route('/api/committee-flow/<flow_id>/blocks/reorder', methods=['POST'])
def reorder_blocks(flow_id):
    """Reorder blocks in the flow"""
    try:
        data = request.json
        block_order = data.get('block_order', [])

        if not block_order:
            return jsonify({'error': 'Block order is required'}), 400

        success = committee_flow_manager.reorder_blocks(flow_id, block_order)
        if not success:
            return jsonify({'error': 'Flow not found'}), 404

        return jsonify({'message': 'Blocks reordered successfully'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/committee-flow/<flow_id>/blocks/<block_id>/start', methods=['POST'])
def start_block(flow_id, block_id):
    """Start/activate a block"""
    try:
        block = committee_flow_manager.start_block(flow_id, block_id)
        if not block:
            return jsonify({'error': 'Block not found'}), 404
        return jsonify(block)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/committee-flow/<flow_id>/blocks/<block_id>/complete', methods=['POST'])
def complete_block(flow_id, block_id):
    """Complete a block"""
    try:
        block = committee_flow_manager.complete_block(flow_id, block_id)
        if not block:
            return jsonify({'error': 'Block not found'}), 404
        return jsonify(block)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/committee-flow/<flow_id>/blocks/<block_id>/notes', methods=['POST'])
def add_block_note(flow_id, block_id):
    """Add a note to a block"""
    try:
        data = request.json
        note = data.get('note', '')

        if not note:
            return jsonify({'error': 'Note text is required'}), 400

        block = committee_flow_manager.add_block_note(flow_id, block_id, note)
        if not block:
            return jsonify({'error': 'Block not found'}), 404

        return jsonify(block)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ============= HEALTH CHECK =============

@app.route('/api/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'ai_provider': ai_service.get_available_provider(),
        'timestamp': datetime.now().isoformat()
    })


@app.route('/chair')
def chair_page():
    return send_from_directory('../frontend', 'chair.html')


@app.route('/delegate')
def delegate_page():
    return send_from_directory('../frontend', 'delegate.html')


if __name__ == '__main__':
    print("\n" + "="*50)
    print("MUNvare Backend Server")
    print("="*50)
    print(f"AI Provider: {ai_service.get_available_provider()}")
    print("Starting server on http://localhost:8000")
    print("="*50 + "\n")

    socketio.run(app, debug=True, host='0.0.0.0', port=8000, allow_unsafe_werkzeug=True)
