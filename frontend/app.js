// MUNvare Frontend JavaScript

const API_BASE = 'http://localhost:5000/api';

// Global state
let chatHistory = [];
let currentNoteId = null;
let currentNote = null;

// ============= Navigation =============

document.addEventListener('DOMContentLoaded', function() {
    // Setup navigation
    document.querySelectorAll('.nav-link').forEach(link => {
        link.addEventListener('click', function(e) {
            e.preventDefault();
            const section = this.dataset.section;
            navigateTo(section);
        });
    });

    // Setup chat input
    document.getElementById('chatInput').addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            sendMessage();
        }
    });

    // Load initial data
    loadSavedSpeeches();
    loadNotes();
    loadPremadeNotes();

    // Check API health
    checkAPIHealth();
});

function navigateTo(section) {
    // Update nav links
    document.querySelectorAll('.nav-link').forEach(link => {
        link.classList.remove('active');
    });
    document.querySelector(`[data-section="${section}"]`).classList.add('active');

    // Update content sections
    document.querySelectorAll('.content-section').forEach(sec => {
        sec.classList.remove('active');
    });
    document.getElementById(section).classList.add('active');
}

// ============= API Health Check =============

async function checkAPIHealth() {
    try {
        const response = await fetch(`${API_BASE}/health`);
        const data = await response.json();
        console.log('API Status:', data);
    } catch (error) {
        console.error('API is not available:', error);
        showNotification('Warning: Backend server not running. Please start the backend.', 'warning');
    }
}

// ============= Chat Functions =============

async function sendMessage() {
    const input = document.getElementById('chatInput');
    const message = input.value.trim();

    if (!message) return;

    // Add user message to UI
    addChatMessage(message, 'user');
    input.value = '';

    // Add to history
    chatHistory.push({ role: 'user', content: message });

    try {
        const response = await fetch(`${API_BASE}/chat`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                message: message,
                history: chatHistory.slice(-10) // Last 10 messages for context
            })
        });

        const data = await response.json();

        // Add assistant message
        addChatMessage(data.response, 'assistant');
        chatHistory.push({ role: 'assistant', content: data.response });

    } catch (error) {
        addChatMessage('Error: Could not connect to server. Please make sure the backend is running.', 'assistant');
    }
}

function addChatMessage(message, role) {
    const messagesContainer = document.getElementById('chatMessages');
    const messageDiv = document.createElement('div');
    messageDiv.className = `chat-message ${role}`;
    messageDiv.textContent = message;
    messagesContainer.appendChild(messageDiv);
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
}

// ============= Speech Generator =============

async function generateSpeech() {
    const country = document.getElementById('speechCountry').value;
    const topic = document.getElementById('speechTopic').value;
    const committee = document.getElementById('speechCommittee').value;
    const stance = document.getElementById('speechStance').value;
    const speechType = document.getElementById('speechType').value;

    if (!country || !topic) {
        showNotification('Please fill in country and topic', 'error');
        return;
    }

    const output = document.getElementById('speechOutput');
    const content = document.getElementById('speechContent');

    content.innerHTML = '<div class="loading"></div> Generating speech...';
    output.style.display = 'block';

    try {
        const response = await fetch(`${API_BASE}/speech/generate`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                country,
                topic,
                committee,
                stance,
                speech_type: speechType
            })
        });

        const data = await response.json();
        content.textContent = data.content;

        // Reload saved speeches
        loadSavedSpeeches();

    } catch (error) {
        content.textContent = 'Error generating speech. Please check your API keys and backend connection.';
    }
}

function copySpeech() {
    const content = document.getElementById('speechContent').textContent;
    navigator.clipboard.writeText(content);
    showNotification('Speech copied to clipboard!', 'success');
}

async function loadSavedSpeeches() {
    try {
        const response = await fetch(`${API_BASE}/speeches`);
        const speeches = await response.json();

        const container = document.getElementById('savedSpeeches');
        container.innerHTML = '';

        speeches.slice(0, 10).forEach(speech => {
            const div = document.createElement('div');
            div.className = 'speech-item';
            div.innerHTML = `
                <div class="speech-item-header">
                    <div class="speech-item-title">${speech.country} - ${speech.topic}</div>
                    <div class="speech-item-date">${new Date(speech.created_at).toLocaleDateString()}</div>
                </div>
                <div class="speech-item-meta">${speech.committee || 'General'} | ${speech.speech_type}</div>
            `;
            div.onclick = () => viewSpeech(speech);
            container.appendChild(div);
        });

    } catch (error) {
        console.error('Error loading speeches:', error);
    }
}

function viewSpeech(speech) {
    document.getElementById('speechContent').textContent = speech.content;
    document.getElementById('speechOutput').style.display = 'block';
}

// ============= Notes Functions =============

async function loadNotes() {
    try {
        const response = await fetch(`${API_BASE}/notes`);
        let notes = await response.json();

        // Filter by folder if one is selected
        if (typeof selectedFolderId !== 'undefined' && selectedFolderId !== null) {
            notes = notes.filter(note => note.folder === selectedFolderId);
        }

        const container = document.getElementById('notesList');
        container.innerHTML = '';

        if (notes.length === 0 && selectedFolderId) {
            container.innerHTML = '<p style="padding: 12px; color: var(--text-secondary); font-size: 13px;">No notes in this folder</p>';
            return;
        }

        notes.forEach(note => {
            const div = document.createElement('div');
            div.className = 'note-item';
            div.draggable = true; // Make note draggable
            div.dataset.noteId = note.id;

            if (currentNoteId === note.id) {
                div.classList.add('active');
            }

            // Show folder badge if note has one
            let folderBadge = '';
            if (note.folder && typeof allFolders !== 'undefined') {
                const folder = allFolders.find(f => f.id === note.folder);
                if (folder) {
                    folderBadge = `<span class="note-folder-badge">${folder.icon}</span>`;
                }
            }

            div.innerHTML = `
                <div class="note-item-title">${folderBadge} ${note.title}</div>
                <div class="note-item-date">${new Date(note.updated_at).toLocaleDateString()}</div>
                <button onclick="showNoteFolderMenu(event, '${note.id}')" class="note-folder-btn" title="Move to folder">📁</button>
            `;

            div.onclick = (e) => {
                if (!e.target.classList.contains('note-folder-btn')) {
                    loadNote(note.id);
                }
            };

            // Drag start event
            div.addEventListener('dragstart', (e) => {
                e.dataTransfer.setData('noteId', note.id);
                div.classList.add('dragging');
            });

            // Drag end event
            div.addEventListener('dragend', () => {
                div.classList.remove('dragging');
            });

            container.appendChild(div);
        });

    } catch (error) {
        console.error('Error loading notes:', error);
    }
}

function showNoteFolderMenu(event, noteId) {
    event.stopPropagation();

    // Remove existing menu if any
    const existingMenu = document.querySelector('.folder-menu');
    if (existingMenu) existingMenu.remove();

    // Create folder menu
    const menu = document.createElement('div');
    menu.className = 'folder-menu';
    menu.style.cssText = `
        position: absolute;
        background: white;
        border: 1px solid #ddd;
        border-radius: 8px;
        padding: 8px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        z-index: 1000;
        min-width: 200px;
    `;

    menu.innerHTML = '<div style="padding: 4px 8px; font-weight: bold; border-bottom: 1px solid #eee; margin-bottom: 4px;">Move to folder:</div>';

    if (typeof allFolders !== 'undefined') {
        allFolders.forEach(folder => {
            const item = document.createElement('div');
            item.style.cssText = 'padding: 8px; cursor: pointer; border-radius: 4px;';
            item.textContent = `${folder.icon} ${folder.name}`;
            item.onmouseover = () => item.style.background = '#f0f0f0';
            item.onmouseout = () => item.style.background = 'transparent';
            item.onclick = () => {
                moveNoteToFolder(noteId, folder.id);
                menu.remove();
            };
            menu.appendChild(item);
        });
    }

    // Position menu
    const rect = event.target.getBoundingClientRect();
    menu.style.left = rect.left + 'px';
    menu.style.top = (rect.bottom + 5) + 'px';

    document.body.appendChild(menu);

    // Close menu on outside click
    setTimeout(() => {
        document.addEventListener('click', function closeMenu() {
            menu.remove();
            document.removeEventListener('click', closeMenu);
        });
    }, 10);
}

async function createNewNote() {
    try {
        const response = await fetch(`${API_BASE}/notes`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                title: 'New Note',
                content: ''
            })
        });

        const note = await response.json();
        currentNoteId = note.id;
        currentNote = note;

        document.getElementById('noteEditor').style.display = 'flex';
        document.getElementById('noteTitle').value = note.title;
        document.getElementById('noteContent').value = note.content;

        loadNotes();

    } catch (error) {
        showNotification('Error creating note', 'error');
    }
}

async function loadNote(noteId) {
    try {
        const response = await fetch(`${API_BASE}/notes/${noteId}`);
        const note = await response.json();

        currentNoteId = noteId;
        currentNote = note;

        document.getElementById('noteEditor').style.display = 'flex';
        document.getElementById('noteTitle').value = note.title;
        document.getElementById('noteContent').value = note.content;

        if (note.analysis) {
            showNoteAnalysis(note.analysis);
        } else {
            document.getElementById('noteAnalysis').style.display = 'none';
        }

        loadNotes();

    } catch (error) {
        showNotification('Error loading note', 'error');
    }
}

async function saveNote() {
    if (!currentNoteId) return;

    const title = document.getElementById('noteTitle').value;
    const content = document.getElementById('noteContent').value;

    try {
        await fetch(`${API_BASE}/notes/${currentNoteId}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ title, content })
        });

        showNotification('Note saved!', 'success');
        loadNotes();

    } catch (error) {
        showNotification('Error saving note', 'error');
    }
}

async function analyzeNote() {
    if (!currentNoteId) return;

    const analysisDiv = document.getElementById('noteAnalysis');
    analysisDiv.innerHTML = '<div class="loading"></div> Analyzing...';
    analysisDiv.style.display = 'block';

    try {
        const response = await fetch(`${API_BASE}/notes/${currentNoteId}/analyze`, {
            method: 'POST'
        });

        const analysis = await response.json();
        showNoteAnalysis(analysis);

    } catch (error) {
        analysisDiv.textContent = 'Error analyzing note';
    }
}

function showNoteAnalysis(analysis) {
    const div = document.getElementById('noteAnalysis');
    div.innerHTML = `
        <h4>AI Analysis</h4>
        <div style="white-space: pre-wrap;">${analysis.analysis}</div>
        <div style="margin-top: 12px; font-size: 13px; color: var(--text-secondary);">
            Word count: ${analysis.word_count} | Reading time: ${analysis.estimated_reading_time}
        </div>
    `;
    div.style.display = 'block';
}

async function deleteNote() {
    if (!currentNoteId || !confirm('Delete this note?')) return;

    try {
        await fetch(`${API_BASE}/notes/${currentNoteId}`, {
            method: 'DELETE'
        });

        currentNoteId = null;
        currentNote = null;
        document.getElementById('noteEditor').style.display = 'none';

        showNotification('Note deleted', 'success');
        loadNotes();

    } catch (error) {
        showNotification('Error deleting note', 'error');
    }
}

// ============= Premade Notes =============

async function loadPremadeNotes() {
    try {
        const response = await fetch(`${API_BASE}/premade-notes`);
        const notes = await response.json();

        const container = document.getElementById('premadeNotesList');
        container.innerHTML = '';

        if (notes.length === 0) {
            container.innerHTML = `
                <div style="padding: 40px; text-align: center; color: var(--text-secondary);">
                    <p>No premade notes yet. Run backend/generate_premade_notes.py to create them.</p>
                </div>
            `;
            return;
        }

        notes.forEach(note => {
            const div = document.createElement('div');
            div.className = 'premade-note-card';
            div.innerHTML = `<h3>${note.title}</h3>`;
            div.onclick = () => viewPremadeNote(note);
            container.appendChild(div);
        });

    } catch (error) {
        console.error('Error loading premade notes:', error);
    }
}

function viewPremadeNote(note) {
    document.getElementById('premadeNotesList').style.display = 'none';
    document.getElementById('premadeNoteViewer').style.display = 'block';
    document.getElementById('premadeNoteTitle').textContent = note.title;
    document.getElementById('premadeNoteContent').innerHTML = renderMarkdown(note.content);
}

function closePremadeNote() {
    document.getElementById('premadeNotesList').style.display = 'grid';
    document.getElementById('premadeNoteViewer').style.display = 'none';
}

function renderMarkdown(text) {
    // Simple markdown rendering
    return text
        .replace(/^### (.+)$/gm, '<h3>$1</h3>')
        .replace(/^## (.+)$/gm, '<h2>$1</h2>')
        .replace(/^# (.+)$/gm, '<h1>$1</h1>')
        .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
        .replace(/\*(.+?)\*/g, '<em>$1</em>')
        .replace(/^- (.+)$/gm, '<li>$1</li>')
        .replace(/(<li>.*<\/li>)/s, '<ul>$1</ul>')
        .replace(/\n\n/g, '</p><p>')
        .replace(/^(?!<[hul])/gm, '<p>')
        .replace(/$/gm, '</p>');
}

// ============= Research Tools =============

async function generatePOI() {
    const country = document.getElementById('poiCountry').value;
    const topic = document.getElementById('poiTopic').value;
    const target = document.getElementById('poiTarget').value;

    if (!country || !topic) {
        showNotification('Please fill in country and topic', 'error');
        return;
    }

    const output = document.getElementById('poiOutput');
    output.innerHTML = '<div class="loading"></div> Generating questions...';
    output.style.display = 'block';

    try {
        const response = await fetch(`${API_BASE}/research/poi`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ country, topic, target_country: target })
        });

        const data = await response.json();
        const html = data.questions.map((q, i) => `<p><strong>${i+1}.</strong> ${q}</p>`).join('');
        output.innerHTML = `<h4>POI Questions</h4>${html}
            <button onclick="saveToNotes('POI Questions - ${country}', \`${html}\`, 'poi')" class="btn btn-secondary" style="margin-top: 12px;">Save to Notes</button>`;

    } catch (error) {
        output.textContent = 'Error generating questions';
    }
}

async function researchForeignPolicy() {
    const country = document.getElementById('fpCountry').value;
    const topic = document.getElementById('fpTopic').value;

    if (!country || !topic) {
        showNotification('Please fill in country and topic', 'error');
        return;
    }

    const output = document.getElementById('fpOutput');
    output.innerHTML = '<div class="loading"></div> Researching...';
    output.style.display = 'block';

    try {
        const response = await fetch(`${API_BASE}/research/foreign-policy`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ country, topic })
        });

        const data = await response.json();
        output.innerHTML = `<h4>Foreign Policy Analysis</h4><div style="white-space: pre-wrap;">${data.policy}</div>
            <button onclick="saveToNotes('Foreign Policy - ${country} - ${topic}', \`${data.policy.replace(/`/g, '\\`')}\`, 'research')" class="btn btn-secondary" style="margin-top: 12px;">Save to Notes</button>`;

    } catch (error) {
        output.textContent = 'Error researching foreign policy';
    }
}

async function suggestModCaucus() {
    const agenda = document.getElementById('mcAgenda').value;
    const committee = document.getElementById('mcCommittee').value;

    if (!agenda) {
        showNotification('Please fill in the agenda', 'error');
        return;
    }

    const output = document.getElementById('mcOutput');
    output.innerHTML = '<div class="loading"></div> Generating suggestions...';
    output.style.display = 'block';

    try {
        const response = await fetch(`${API_BASE}/research/modcaucus`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ agenda, committee })
        });

        const data = await response.json();
        const html = data.topics.map((t, i) => `<p><strong>${i+1}.</strong> ${t}</p>`).join('');
        output.innerHTML = `<h4>Suggested Topics</h4>${html}
            <button onclick="saveToNotes('ModCaucus Topics - ${agenda}', \`${html}\`, 'general')" class="btn btn-secondary" style="margin-top: 12px;">Save to Notes</button>`;

    } catch (error) {
        output.textContent = 'Error generating suggestions';
    }
}

async function generateCountryProfile() {
    const country = document.getElementById('profileCountry').value;
    const topic = document.getElementById('profileTopic').value;

    if (!country) {
        showNotification('Please enter a country', 'error');
        return;
    }

    const output = document.getElementById('profileOutput');
    output.innerHTML = '<div class="loading"></div> Generating profile...';
    output.style.display = 'block';

    try {
        const response = await fetch(`${API_BASE}/research/country-profile`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ country, topic })
        });

        const data = await response.json();
        output.innerHTML = `<h4>Country Profile: ${country}</h4><div style="white-space: pre-wrap;">${data.profile}</div>
            <button onclick="saveToNotes('Country Profile - ${country}', \`${data.profile.replace(/`/g, '\\`')}\`, 'research')" class="btn btn-secondary" style="margin-top: 12px;">Save to Notes</button>`;

    } catch (error) {
        output.textContent = 'Error generating profile';
    }
}

async function generateResolution() {
    const topic = document.getElementById('resolutionTopic').value;
    const committee = document.getElementById('resolutionCommittee').value;
    const country = document.getElementById('resolutionCountry').value;

    if (!topic) {
        showNotification('Please enter a topic', 'error');
        return;
    }

    const output = document.getElementById('resolutionOutput');
    output.innerHTML = '<div class="loading"></div> Building resolution...';
    output.style.display = 'block';

    try {
        const response = await fetch(`${API_BASE}/research/resolution-builder`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ topic, committee, country })
        });

        const data = await response.json();
        output.innerHTML = `<h4>Draft Resolution</h4><div style="white-space: pre-wrap;">${data.resolution}</div>
            <button onclick="saveToNotes('Resolution Draft - ${topic}', \`${data.resolution.replace(/`/g, '\\`')}\`, 'documentation')" class="btn btn-secondary" style="margin-top: 12px;">Save to Notes</button>`;

    } catch (error) {
        output.textContent = 'Error generating resolution';
    }
}

async function generateCrisisResponse() {
    const country = document.getElementById('crisisCountry').value;
    const crisis = document.getElementById('crisisDescription').value;

    if (!country || !crisis) {
        showNotification('Please fill in all fields', 'error');
        return;
    }

    const output = document.getElementById('crisisOutput');
    output.innerHTML = '<div class="loading"></div> Generating response...';
    output.style.display = 'block';

    try {
        const response = await fetch(`${API_BASE}/research/crisis-response`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ country, crisis })
        });

        const data = await response.json();
        output.innerHTML = `<h4>Crisis Response</h4><div style="white-space: pre-wrap;">${data.response}</div>
            <button onclick="saveToNotes('Crisis Response - ${country}', \`${data.response.replace(/`/g, '\\`')}\`, 'general')" class="btn btn-secondary" style="margin-top: 12px;">Save to Notes</button>`;

    } catch (error) {
        output.textContent = 'Error generating response';
    }
}

async function prepareDebate() {
    const myCountry = document.getElementById('debateMyCountry').value;
    const opponent = document.getElementById('debateOpponent').value;
    const topic = document.getElementById('debateTopic').value;

    if (!myCountry || !opponent || !topic) {
        showNotification('Please fill in all fields', 'error');
        return;
    }

    const output = document.getElementById('debateOutput');
    output.innerHTML = '<div class="loading"></div> Preparing debate strategy...';
    output.style.display = 'block';

    try {
        const response = await fetch(`${API_BASE}/research/debate-prep`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ my_country: myCountry, opponent_country: opponent, topic })
        });

        const data = await response.json();
        output.innerHTML = `<h4>Debate Preparation</h4><div style="white-space: pre-wrap;">${data.preparation}</div>
            <button onclick="saveToNotes('Debate Prep vs ${opponent}', \`${data.preparation.replace(/`/g, '\\`')}\`, 'general')" class="btn btn-secondary" style="margin-top: 12px;">Save to Notes</button>`;

    } catch (error) {
        output.textContent = 'Error preparing debate';
    }
}

async function findAllies() {
    const country = document.getElementById('allyCountry').value;
    const topic = document.getElementById('allyTopic').value;

    if (!country || !topic) {
        showNotification('Please fill in all fields', 'error');
        return;
    }

    const output = document.getElementById('allyOutput');
    output.innerHTML = '<div class="loading"></div> Finding allies and opposition...';
    output.style.display = 'block';

    try {
        // Call both allies and opposition endpoints
        const alliesResp = await fetch(`${API_BASE}/research/allies`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ country, topic })
        });

        const opponentResp = await fetch(`${API_BASE}/research/opposition`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ country, topic })
        });

        const alliesData = await alliesResp.json();
        const opponentData = await opponentResp.json();

        const combinedHTML = `
            <h4>Potential Allies</h4>
            <div style="white-space: pre-wrap;">${alliesData.allies || 'No data'}</div>
            <h4 style="margin-top: 20px;">Opposition Analysis</h4>
            <div style="white-space: pre-wrap;">${opponentData.opposition || 'No data'}</div>
        `;

        output.innerHTML = combinedHTML + `
            <button onclick="saveToNotes('Allies & Opposition - ${topic}', \`${combinedHTML.replace(/`/g, '\\`')}\`, 'lobbying')" class="btn btn-secondary" style="margin-top: 12px;">Save to Notes</button>`;

    } catch (error) {
        output.textContent = 'Error finding allies';
    }
}

async function doComprehensiveResearch() {
    const country = document.getElementById('autoCountry').value;
    const topic = document.getElementById('autoTopic').value;
    const committee = document.getElementById('autoCommittee').value;

    if (!country || !topic) {
        showNotification('Please fill in country and topic', 'error');
        return;
    }

    const output = document.getElementById('autoResearchOutput');
    output.innerHTML = '<div class="loading"></div> Generating comprehensive research... This will take 1-2 minutes as we create detailed strategic notes...';
    output.style.display = 'block';

    try {
        const response = await fetch(`${API_BASE}/research/comprehensive`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ country, topic, committee })
        });

        const data = await response.json();

        if (data.error) {
            output.innerHTML = `<p style="color: var(--danger);">Error: ${data.error}</p>`;
            showNotification('Error generating research', 'error');
            return;
        }

        // Show success message with created notes
        let html = `<h3 style="color: var(--success);">✓ Research Complete!</h3>`;
        html += `<p style="font-size: 16px; margin: 12px 0;"><strong>${data.notes_created.length} detailed strategic notes</strong> have been automatically saved to your folders!</p>`;

        html += '<div style="background: var(--bg-secondary); padding: 16px; border-radius: 8px; margin-top: 16px;">';
        html += '<h4>Notes Created:</h4>';
        html += '<ul style="list-style: none; padding: 0;">';

        data.notes_created.forEach(note => {
            const folderIcons = {
                'lobbying': '🤝',
                'research': '🔍',
                'documentation': '📄',
                'poi': '❓'
            };
            const icon = folderIcons[note.folder] || '📝';
            html += `<li style="padding: 8px; margin: 4px 0; background: var(--bg-tertiary); border-radius: 4px;">
                ${icon} <strong>${note.title}</strong>
                <div style="font-size: 12px; color: var(--text-secondary); margin-top: 4px;">
                    ${note.content.substring(0, 150)}...
                </div>
            </li>`;
        });

        html += '</ul></div>';

        html += `<p style="margin-top: 20px; padding: 12px; background: var(--bg-secondary); border-radius: 8px;">
            <strong>Next Steps:</strong><br>
            1. Go to the "My Notes" section to view all generated research<br>
            2. Click on folders to see notes by category<br>
            3. Use these notes when chatting with AI or generating speeches<br>
            4. Explore individual research tools for even more specific analysis
        </p>`;

        output.innerHTML = html;
        showNotification(`${data.notes_created.length} research notes created!`, 'success');

        // Reload notes in the background
        loadNotes();

    } catch (error) {
        output.innerHTML = `<p style="color: var(--danger);">Error: ${error.message}</p>`;
        showNotification('Error generating research', 'error');
    }
}

async function saveToNotes(title, content, folder) {
    try {
        // Remove HTML tags from content
        const tempDiv = document.createElement('div');
        tempDiv.innerHTML = content;
        const cleanContent = tempDiv.textContent || tempDiv.innerText || content;

        const response = await fetch(`${API_BASE}/notes/save-research`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ title, content: cleanContent, folder })
        });

        if (response.ok) {
            showNotification('Saved to notes!', 'success');
            loadNotes();
        } else {
            showNotification('Error saving to notes', 'error');
        }
    } catch (error) {
        showNotification('Error saving to notes', 'error');
    }
}

// ============= Speech Rating (Placeholder) =============

let mediaRecorder;
let audioChunks = [];

function startRecording() {
    showNotification('Speech recording feature requires backend integration with speech-to-text service', 'warning');
    // This would integrate with the existing SpeechtoText.py module
    // For now, showing as placeholder
}

function stopRecording() {
    showNotification('Recording stopped', 'info');
}

// ============= Search =============

async function searchBook() {
    const query = document.getElementById('searchQuery').value;

    if (!query) {
        showNotification('Please enter a search query', 'error');
        return;
    }

    const results = document.getElementById('searchResults');
    results.innerHTML = '<div class="loading"></div> Searching...';

    try {
        const response = await fetch(`${API_BASE}/search`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ query })
        });

        const data = await response.json();

        if (data.results.length === 0) {
            results.innerHTML = '<p>No results found</p>';
            return;
        }

        results.innerHTML = data.results.map(result => `
            <div class="search-result-item">
                <div class="search-result-section">${result.metadata.section_title || 'MUN Book'}</div>
                <div class="search-result-content">${result.content}</div>
            </div>
        `).join('');

    } catch (error) {
        results.textContent = 'Error searching';
    }
}

// ============= Utilities =============

function showNotification(message, type = 'info') {
    console.log(`[${type.toUpperCase()}] ${message}`);
    // You could implement a toast notification system here
}
