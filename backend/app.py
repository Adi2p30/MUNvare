from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import os
import json
from datetime import datetime
from vectordb import initialize_vector_db
from ai_service import AIService
from config_manager import ConfigManager
from chat_manager import ChatManager
from notes_manager import NotesManager
import sys

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

app = Flask(__name__, static_folder='../frontend', static_url_path='')
CORS(app)

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

# Data storage directories
DATA_DIR = os.path.join(os.path.dirname(__file__), '..', 'data')
NOTES_DIR = os.path.join(DATA_DIR, 'notes')
SPEECHES_DIR = os.path.join(DATA_DIR, 'speeches')
PREMADE_NOTES_DIR = os.path.join(DATA_DIR, 'premade_notes')

for directory in [DATA_DIR, NOTES_DIR, SPEECHES_DIR, PREMADE_NOTES_DIR]:
    os.makedirs(directory, exist_ok=True)


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
        speech_id = f"speech_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
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

            note_id = f"note_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            note_data = {
                'id': note_id,
                'title': title,
                'content': content,
                'created_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat(),
                'analysis': None
            }

            note_file = os.path.join(NOTES_DIR, f"{note_id}.json")
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
    """Generate POI questions"""
    try:
        data = request.json
        country = data.get('country', '')
        topic = data.get('topic', '')
        target_country = data.get('target_country', '')

        if not country or not topic:
            return jsonify({'error': 'Country and topic are required'}), 400

        questions = ai_service.generate_poi_questions(country, topic, target_country)

        return jsonify({
            'questions': questions,
            'country': country,
            'topic': topic,
            'target_country': target_country
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/research/foreign-policy', methods=['POST'])
def research_foreign_policy():
    """Research foreign policy"""
    try:
        data = request.json
        country = data.get('country', '')
        topic = data.get('topic', '')

        if not country or not topic:
            return jsonify({'error': 'Country and topic are required'}), 400

        policy = ai_service.research_foreign_policy(country, topic)

        return jsonify({
            'policy': policy,
            'country': country,
            'topic': topic
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/research/modcaucus', methods=['POST'])
def suggest_modcaucus():
    """Suggest moderated caucus topics"""
    try:
        data = request.json
        agenda = data.get('agenda', '')
        committee = data.get('committee', '')

        if not agenda:
            return jsonify({'error': 'Agenda is required'}), 400

        topics = ai_service.suggest_moderated_caucus_topics(agenda, committee)

        return jsonify({
            'topics': topics,
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
    """Get comprehensive country profile"""
    try:
        data = request.json
        country = data.get('country', '')
        topic = data.get('topic', '')

        if not country:
            return jsonify({'error': 'Country is required'}), 400

        profile = ai_service.generate_country_profile(country, topic)
        return jsonify({'profile': profile, 'country': country})

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
    """Generate crisis response"""
    try:
        data = request.json
        country = data.get('country', '')
        crisis = data.get('crisis', '')

        if not country or not crisis:
            return jsonify({'error': 'Country and crisis are required'}), 400

        response_text = ai_service.generate_crisis_response(country, crisis)
        return jsonify({'response': response_text})

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/research/debate-prep', methods=['POST'])
def debate_prep():
    """Prepare for debate against specific country"""
    try:
        data = request.json
        my_country = data.get('my_country', '')
        opponent_country = data.get('opponent_country', '')
        topic = data.get('topic', '')

        if not my_country or not opponent_country or not topic:
            return jsonify({'error': 'All fields are required'}), 400

        prep = ai_service.prepare_debate(my_country, opponent_country, topic)
        return jsonify({'preparation': prep})

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/research/allies', methods=['POST'])
def get_allies():
    """Get potential allies"""
    try:
        data = request.json
        country = data.get('country', '')
        topic = data.get('topic', '')

        if not country or not topic:
            return jsonify({'error': 'Country and topic are required'}), 400

        allies = ai_service.suggest_allies(country, topic)
        return jsonify({'allies': allies})

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/research/opposition', methods=['POST'])
def get_opposition():
    """Get potential opposition"""
    try:
        data = request.json
        country = data.get('country', '')
        topic = data.get('topic', '')

        if not country or not topic:
            return jsonify({'error': 'Country and topic are required'}), 400

        opposition = ai_service.identify_opposition(country, topic)
        return jsonify({'opposition': opposition})

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

        return jsonify(note_data), 201

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


if __name__ == '__main__':
    print("\n" + "="*50)
    print("MUNvare Backend Server")
    print("="*50)
    print(f"AI Provider: {ai_service.get_available_provider()}")
    print("Starting server on http://localhost:5000")
    print("="*50 + "\n")

    app.run(debug=True, host='0.0.0.0', port=5000)
