// MUNvare Frontend JavaScript

const API_BASE = 'http://localhost:8000/api';

// Global state
let chatHistory = [];
let currentNoteId = null;
let currentNote = null;

// ============= Helper Functions for Icons =============

function getHeroIcon(name, size = 'sm') {
    const icons = {
        'folder': '<svg class="icon icon-__SIZE__" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-6l-2-2H5a2 2 0 00-2 2z"/></svg>',
        'save': '<svg class="icon icon-__SIZE__" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 7H5a2 2 0 00-2 2v9a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-3m-1 4l-3 3m0 0l-3-3m3 3V4"/></svg>',
        'search': '<svg class="icon icon-__SIZE__" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"/></svg>',
        'document': '<svg class="icon icon-__SIZE__" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"/></svg>',
        'users': '<svg class="icon icon-__SIZE__" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z"/></svg>',
        'pencil': '<svg class="icon icon-__SIZE__" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z"/></svg>',
        'questionMarkCircle': '<svg class="icon icon-__SIZE__" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8.228 9c.549-1.165 2.03-2 3.772-2 2.21 0 4 1.343 4 3 0 1.4-1.278 2.575-3.006 2.907-.542.104-.994.54-.994 1.093m0 3h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"/></svg>',
        'checkCircle': '<svg class="icon icon-__SIZE__" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"/></svg>',
        'exclamationCircle': '<svg class="icon icon-__SIZE__" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"/></svg>',
        'trophy': '<svg class="icon icon-__SIZE__" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4M7.835 4.697a3.42 3.42 0 001.946-.806 3.42 3.42 0 014.438 0 3.42 3.42 0 001.946.806 3.42 3.42 0 013.138 3.138 3.42 3.42 0 00.806 1.946 3.42 3.42 0 010 4.438 3.42 3.42 0 00-.806 1.946 3.42 3.42 0 01-3.138 3.138 3.42 3.42 0 00-1.946.806 3.42 3.42 0 01-4.438 0 3.42 3.42 0 00-1.946-.806 3.42 3.42 0 01-3.138-3.138 3.42 3.42 0 00-.806-1.946 3.42 3.42 0 010-4.438 3.42 3.42 0 00.806-1.946 3.42 3.42 0 013.138-3.138z"/></svg>',
        'trash': '<svg class="icon icon-__SIZE__" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"/></svg>',
        'calendar': '<svg class="icon icon-__SIZE__" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z"/></svg>',
    };

    return (icons[name] || icons['folder']).replace('__SIZE__', size);
}

function getFolderIcon(folderId, size = 'sm') {
    const folderIcons = {
        'lobbying': getHeroIcon('users', size),
        'research': getHeroIcon('search', size),
        'documentation': getHeroIcon('document', size),
        'poi': getHeroIcon('questionMarkCircle', size),
        'general': getHeroIcon('folder', size),
    };
    return folderIcons[folderId] || getHeroIcon('pencil', size);
}

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
    console.log('Navigating to:', section);

    // Hide/show sidebar based on section
    if (section === 'start-screen') {
        document.body.classList.add('on-start-screen');
    } else {
        document.body.classList.remove('on-start-screen');
    }

    // Update nav links
    document.querySelectorAll('.nav-link').forEach(link => {
        link.classList.remove('active');
    });

    // Only update nav link if it exists
    const navLink = document.querySelector(`[data-section="${section}"]`);
    if (navLink) {
        navLink.classList.add('active');
    }

    // Update content sections
    document.querySelectorAll('.content-section').forEach(sec => {
        sec.classList.remove('active');
    });

    const targetSection = document.getElementById(section);
    if (targetSection) {
        targetSection.classList.add('active');
        console.log('Successfully navigated to:', section);
    } else {
        console.error('Section not found:', section);
    }
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
        if (!response.ok || !Array.isArray(speeches)) {
            console.error('Error loading speeches:', speeches);
            return;
        }

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
        if (!response.ok || !Array.isArray(notes)) {
            console.error('Error loading notes:', notes);
            return;
        }

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
                <button onclick="showNoteFolderMenu(event, '${note.id}')" class="note-folder-btn" title="Move to folder">${getHeroIcon('folder', 'sm')}</button>
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

        // Reset to edit mode
        toggleNoteView('edit');

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

function toggleNoteView(mode) {
    const editBtn = document.getElementById('editModeBtn');
    const previewBtn = document.getElementById('previewModeBtn');
    const contentArea = document.getElementById('noteContent');
    const previewArea = document.getElementById('notePreview');

    if (mode === 'edit') {
        editBtn.classList.add('btn-primary');
        editBtn.classList.remove('btn-secondary');
        previewBtn.classList.remove('btn-primary');
        previewBtn.classList.add('btn-secondary');
        contentArea.style.display = 'block';
        previewArea.style.display = 'none';
    } else {
        previewBtn.classList.add('btn-primary');
        previewBtn.classList.remove('btn-secondary');
        editBtn.classList.remove('btn-primary');
        editBtn.classList.add('btn-secondary');
        contentArea.style.display = 'none';
        previewArea.style.display = 'block';

        // Render markdown
        const markdown = contentArea.value;
        previewArea.innerHTML = renderMarkdown(markdown);
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
    // Use marked.js for markdown rendering if available
    if (typeof marked !== 'undefined') {
        marked.setOptions({
            breaks: true,
            gfm: true
        });
        return marked.parse(text);
    }

    // Fallback simple markdown rendering
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
        const markdown = data.questions.map((q, i) => `**${i+1}.** ${q}`).join('\n\n');
        const html = renderMarkdown(markdown);
        output.innerHTML = `
            <h4>POI Questions</h4>
            <div class="markdown-content">${html}</div>
            <button onclick="saveResearchToNotes('POI Questions - ${country}', \`${markdown.replace(/`/g, '\\`')}\`, 'poi')" class="btn btn-primary" style="margin-top: 16px;">💾 Save to Notes (POI Folder)</button>
        `;

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
        const html = renderMarkdown(data.policy);
        output.innerHTML = `
            <h4>Foreign Policy Analysis</h4>
            <div class="markdown-content">${html}</div>
            <button onclick="saveResearchToNotes('Foreign Policy - ${country} - ${topic}', \`${data.policy.replace(/`/g, '\\`')}\`, 'research')" class="btn btn-primary" style="margin-top: 16px;">💾 Save to Notes (Research Folder)</button>
        `;

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
        const markdown = data.topics.map((t, i) => `**${i+1}.** ${t}`).join('\n\n');
        const html = renderMarkdown(markdown);
        output.innerHTML = `
            <h4>Suggested Topics</h4>
            <div class="markdown-content">${html}</div>
            <button onclick="saveResearchToNotes('ModCaucus Topics - ${agenda}', \`${markdown.replace(/`/g, '\\`')}\`, 'general')" class="btn btn-primary" style="margin-top: 16px;">💾 Save to Notes (General Folder)</button>
        `;

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
        const html = renderMarkdown(data.profile);
        output.innerHTML = `
            <h4>Country Profile: ${country}</h4>
            <div class="markdown-content">${html}</div>
            <button onclick="saveResearchToNotes('Country Profile - ${country}', \`${data.profile.replace(/`/g, '\\`')}\`, 'research')" class="btn btn-primary" style="margin-top: 16px;">💾 Save to Notes (Research Folder)</button>
        `;

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
        const html = renderMarkdown(data.resolution);
        output.innerHTML = `
            <h4>Draft Resolution</h4>
            <div class="markdown-content">${html}</div>
            <button onclick="saveResearchToNotes('Resolution Draft - ${topic}', \`${data.resolution.replace(/`/g, '\\`')}\`, 'documentation')" class="btn btn-primary" style="margin-top: 16px;">💾 Save to Notes (Documentation Folder)</button>
        `;

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
        const html = renderMarkdown(data.response);
        output.innerHTML = `
            <h4>Crisis Response</h4>
            <div class="markdown-content">${html}</div>
            <button onclick="saveResearchToNotes('Crisis Response - ${country}', \`${data.response.replace(/`/g, '\\`')}\`, 'general')" class="btn btn-primary" style="margin-top: 16px;">💾 Save to Notes (General Folder)</button>
        `;

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
        const html = renderMarkdown(data.preparation);
        output.innerHTML = `
            <h4>Debate Preparation</h4>
            <div class="markdown-content">${html}</div>
            <button onclick="saveResearchToNotes('Debate Prep vs ${opponent}', \`${data.preparation.replace(/`/g, '\\`')}\`, 'general')" class="btn btn-primary" style="margin-top: 16px;">💾 Save to Notes (General Folder)</button>
        `;

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

        const combinedMarkdown = `## Potential Allies\n\n${alliesData.allies || 'No data'}\n\n## Opposition Analysis\n\n${opponentData.opposition || 'No data'}`;
        const html = renderMarkdown(combinedMarkdown);

        output.innerHTML = `
            <div class="markdown-content">${html}</div>
            <button onclick="saveResearchToNotes('Allies & Opposition - ${topic}', \`${combinedMarkdown.replace(/`/g, '\\`')}\`, 'lobbying')" class="btn btn-primary" style="margin-top: 16px;">💾 Save to Notes (Lobbying Folder)</button>
        `;

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
        let html = `<h3 style="color: var(--success);">Research Complete!</h3>`;
        html += `<p style="font-size: 16px; margin: 12px 0;"><strong>${data.notes_created.length} detailed strategic notes</strong> have been automatically saved to your folders!</p>`;

        html += '<div style="background: var(--bg-secondary); padding: 16px; border-radius: 8px; margin-top: 16px;">';
        html += '<h4>Notes Created:</h4>';
        html += '<ul style="list-style: none; padding: 0;">';

        data.notes_created.forEach(note => {
            const icon = getFolderIcon(note.folder, 'sm');
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

async function saveResearchToNotes(title, content, folder) {
    try {
        // Get the folder name mapping
        const folderMapping = {
            'poi': 'POI',
            'research': 'Research',
            'lobbying': 'Lobbying',
            'documentation': 'Documentation',
            'general': 'General'
        };

        const response = await fetch(`${API_BASE}/notes/save-research`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ title, content, folder })
        });

        if (response.ok) {
            const folderName = folderMapping[folder] || folder;
            showNotification(`✅ Saved to ${folderName} folder!`, 'success');
            loadNotes();

            // Optionally switch to notes section to show the saved note
            setTimeout(() => {
                if (confirm(`Research saved! Would you like to view your notes?`)) {
                    navigateTo('notes');
                }
            }, 500);
        } else {
            showNotification('Error saving to notes', 'error');
        }
    } catch (error) {
        console.error('Error saving research to notes:', error);
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

// ============= STREAMING SUPPORT =============

/**
 * Handle Server-Sent Events (SSE) streaming
 * @param {string} url - API endpoint URL
 * @param {object} data - Request data
 * @param {function} onProgress - Callback for progress updates
 * @param {function} onComplete - Callback when complete
 * @param {function} onError - Callback for errors
 */
function streamRequest(url, data, onProgress, onComplete, onError) {
    // Use fetch with ReadableStream for SSE
    fetch(url, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'Accept': 'text/event-stream'
        },
        body: JSON.stringify(data)
    }).then(response => {
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let buffer = '';

        function processStream() {
            reader.read().then(({ done, value }) => {
                if (done) {
                    return;
                }

                // Decode the chunk and add to buffer
                buffer += decoder.decode(value, { stream: true });

                // Process complete SSE messages
                const lines = buffer.split('\n\n');
                buffer = lines.pop() || ''; // Keep incomplete message in buffer

                lines.forEach(line => {
                    if (line.startsWith('data: ')) {
                        try {
                            const jsonStr = line.substring(6); // Remove 'data: ' prefix
                            const eventData = JSON.parse(jsonStr);

                            if (eventData.stage === 'complete') {
                                onComplete(eventData);
                            } else if (eventData.stage === 'error') {
                                onError(eventData.error || 'Unknown error');
                            } else {
                                onProgress(eventData);
                            }
                        } catch (e) {
                            console.error('Error parsing SSE message:', e);
                        }
                    }
                });

                // Continue reading
                processStream();
            }).catch(error => {
                onError(error.message || 'Stream error');
            });
        }

        processStream();

    }).catch(error => {
        onError(error.message || 'Connection error');
    });
}

/**
 * Execute comprehensive research pipeline with streaming progress
 */
async function executeComprehensiveStreamingResearch() {
    const country = document.getElementById('autoCountry')?.value;
    const topic = document.getElementById('autoTopic')?.value;
    const committee = document.getElementById('autoCommittee')?.value;

    if (!country || !topic) {
        showNotification('Please fill in country and topic', 'error');
        return;
    }

    const output = document.getElementById('autoResearchOutput');
    output.style.display = 'block';
    output.innerHTML = '<div class="streaming-progress"></div>';

    const progressContainer = output.querySelector('.streaming-progress');
    const stages = [];

    // Progress callback
    function onProgress(update) {
        console.log('Progress:', update);

        // Find or create stage element
        let stageElement = progressContainer.querySelector(`[data-stage="${update.stage}"]`);

        if (!stageElement) {
            stageElement = document.createElement('div');
            stageElement.className = 'streaming-stage';
            stageElement.setAttribute('data-stage', update.stage);
            progressContainer.appendChild(stageElement);
        }

        // Update stage content
        const statusIcon = update.message.startsWith('✓') ? '✓' :
                          update.message.startsWith('✗') ? '✗' : '⏳';

        stageElement.innerHTML = `
            <span class="stage-icon">${statusIcon}</span>
            <span class="stage-message">${update.message}</span>
        `;

        // Add success/error styling
        if (update.message.startsWith('✓')) {
            stageElement.classList.add('stage-complete');
        } else if (update.message.startsWith('✗')) {
            stageElement.classList.add('stage-error');
        }
    }

    // Complete callback
    function onComplete(result) {
        console.log('Complete:', result);

        const finalOutput = result.data?.formatted_output || result.data?.output || 'Research complete!';

        output.innerHTML = `
            <div class="stream-complete">
                <h3 style="color: var(--success);">✅ Comprehensive Research Complete!</h3>
                <div class="research-output">
                    ${marked.parse ? marked.parse(finalOutput) : finalOutput}
                </div>
                <button class="btn btn-primary" onclick="saveCurrentResearch('${country}', '${topic}')">
                    Save to Notes
                </button>
            </div>
        `;

        showNotification('Research pipeline completed!', 'success');
        loadNotes(); // Refresh notes list
    }

    // Error callback
    function onError(error) {
        console.error('Streaming error:', error);
        output.innerHTML = `
            <div class="stream-error">
                <p style="color: var(--danger);">❌ Error: ${error}</p>
                <button class="btn btn-secondary" onclick="executeComprehensiveStreamingResearch()">
                    Retry
                </button>
            </div>
        `;
        showNotification('Error in research pipeline', 'error');
    }

    // Start streaming
    streamRequest(
        `${API_BASE}/research/comprehensive-stream`,
        { country, topic, committee },
        onProgress,
        onComplete,
        onError
    );
}

/**
 * Execute crisis response pipeline with streaming
 */
async function executeCrisisStreamingResponse() {
    const country = prompt('Enter your country:');
    const crisis = prompt('Describe the crisis situation:');

    if (!country || !crisis) {
        showNotification('Country and crisis description required', 'error');
        return;
    }

    const output = document.getElementById('autoResearchOutput');
    output.style.display = 'block';
    output.innerHTML = '<div class="streaming-progress crisis-mode"></div>';

    const progressContainer = output.querySelector('.streaming-progress');

    streamRequest(
        `${API_BASE}/research/crisis-stream`,
        { country, crisis },
        (update) => {
            let stageElement = progressContainer.querySelector(`[data-stage="${update.stage}"]`);
            if (!stageElement) {
                stageElement = document.createElement('div');
                stageElement.className = 'streaming-stage crisis';
                stageElement.setAttribute('data-stage', update.stage);
                progressContainer.appendChild(stageElement);
            }

            const statusIcon = update.message.startsWith('✓') ? '✓' : '🚨';
            stageElement.innerHTML = `
                <span class="stage-icon">${statusIcon}</span>
                <span class="stage-message">${update.message}</span>
            `;

            if (update.message.startsWith('✓')) {
                stageElement.classList.add('stage-complete');
            }
        },
        (result) => {
            const finalOutput = result.data?.formatted_output || result.data?.output || 'Crisis response ready!';
            output.innerHTML = `
                <div class="stream-complete crisis-complete">
                    <h3>🚨 Crisis Response Plan Ready</h3>
                    <div class="research-output">${marked.parse ? marked.parse(finalOutput) : finalOutput}</div>
                </div>
            `;
            showNotification('Crisis response generated!', 'success');
        },
        (error) => {
            output.innerHTML = `<p style="color: var(--danger);">❌ Error: ${error}</p>`;
            showNotification('Error generating crisis response', 'error');
        }
    );
}

/**
 * Execute debate mastery pipeline with streaming
 */
async function executeDebateMasteryStreaming() {
    const country = prompt('Enter your country:');
    const topic = prompt('Enter debate topic:');
    const opponent = prompt('Enter opponent country (optional):') || '';

    if (!country || !topic) {
        showNotification('Country and topic required', 'error');
        return;
    }

    const output = document.getElementById('autoResearchOutput');
    output.style.display = 'block';
    output.innerHTML = '<div class="streaming-progress debate-mode"></div>';

    const progressContainer = output.querySelector('.streaming-progress');

    streamRequest(
        `${API_BASE}/research/debate-mastery-stream`,
        { country, topic, opponent_country: opponent },
        (update) => {
            let stageElement = progressContainer.querySelector(`[data-stage="${update.stage}"]`);
            if (!stageElement) {
                stageElement = document.createElement('div');
                stageElement.className = 'streaming-stage debate';
                stageElement.setAttribute('data-stage', update.stage);
                progressContainer.appendChild(stageElement);
            }

            const statusIcon = update.message.startsWith('✓') ? '✓' : '🎭';
            stageElement.innerHTML = `
                <span class="stage-icon">${statusIcon}</span>
                <span class="stage-message">${update.message}</span>
            `;

            if (update.message.startsWith('✓')) {
                stageElement.classList.add('stage-complete');
            }
        },
        (result) => {
            const finalOutput = result.data?.formatted_output || result.data?.output || 'Debate package ready!';
            output.innerHTML = `
                <div class="stream-complete debate-complete">
                    <h3>🏆 Debate Mastery Package Ready</h3>
                    <div class="research-output">${marked.parse ? marked.parse(finalOutput) : finalOutput}</div>
                </div>
            `;
            showNotification('Debate preparation complete!', 'success');
        },
        (error) => {
            output.innerHTML = `<p style="color: var(--danger);">❌ Error: ${error}</p>`;
            showNotification('Error generating debate prep', 'error');
        }
    );
}

// Add window functions for global access
window.executeComprehensiveStreamingResearch = executeComprehensiveStreamingResearch;
window.executeCrisisStreamingResponse = executeCrisisStreamingResponse;
window.executeDebateMasteryStreaming = executeDebateMasteryStreaming;
