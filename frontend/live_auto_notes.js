// Live Auto-Notes - Real-time transcription with AI-powered note generation
// Continuously transcribes, processes with agents, and displays important notes

let autoNotesRecognition = null;
let isAutoNotesActive = false;
let transcriptBuffer = '';
let lastProcessedTime = Date.now();
let processingInterval = null;
let fadeInterval = null;
let currentEventSource = null;
let accumulatedNotes = [];

const CHUNK_INTERVAL = 10000; // Process every 10 seconds
const FADE_INTERVAL = 60000; // Fade notes every 60 seconds
const IMPORTANCE_THRESHOLD = 7; // Only show notes with importance >= 7

// ============= Main Controls =============

function startLiveAutoNotes() {
    if (!('webkitSpeechRecognition' in window) && !('SpeechRecognition' in window)) {
        showNotification('Speech recognition not supported in this browser. Please use Chrome or Edge.', 'error');
        return;
    }

    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    autoNotesRecognition = new SpeechRecognition();
    autoNotesRecognition.continuous = true;
    autoNotesRecognition.interimResults = true;
    autoNotesRecognition.lang = 'en-US';

    const speaker = document.getElementById('autoNotesSpeaker').value || 'Unknown Speaker';
    const liveTranscript = document.getElementById('liveTranscriptText');
    const statusIndicator = document.getElementById('autoNotesStatus');

    autoNotesRecognition.onstart = () => {
        isAutoNotesActive = true;
        transcriptBuffer = '';
        lastProcessedTime = Date.now();

        // Update UI
        document.getElementById('startAutoNotesBtn').style.display = 'none';
        document.getElementById('stopAutoNotesBtn').style.display = 'inline-block';
        statusIndicator.innerHTML = '<span style="color: var(--danger);">● LIVE</span>';
        statusIndicator.style.display = 'inline-block';

        liveTranscript.innerHTML = '<p style="color: var(--text-secondary);">Listening...</p>';

        // Start periodic processing
        processingInterval = setInterval(processTranscriptChunk, CHUNK_INTERVAL);

        // Start periodic fade animation
        fadeInterval = setInterval(startFadeAnimation, FADE_INTERVAL);

        showNotification('Live Auto-Notes started', 'success');
    };

    autoNotesRecognition.onresult = (event) => {
        let interimTranscript = '';
        let finalTranscript = '';

        for (let i = event.resultIndex; i < event.results.length; i++) {
            const transcript = event.results[i][0].transcript;
            if (event.results[i].isFinal) {
                finalTranscript += transcript + ' ';
            } else {
                interimTranscript += transcript;
            }
        }

        if (finalTranscript) {
            transcriptBuffer += finalTranscript;
        }

        // Update live transcript display
        const displayText = transcriptBuffer + interimTranscript;
        liveTranscript.innerHTML = displayText || '<p style="color: var(--text-secondary);">Listening...</p>';
        liveTranscript.scrollTop = liveTranscript.scrollHeight;

        // Auto-process if we have enough content and enough time has passed
        const timeSinceLastProcess = Date.now() - lastProcessedTime;
        if (finalTranscript && transcriptBuffer.split(' ').length >= 50 && timeSinceLastProcess >= CHUNK_INTERVAL) {
            processTranscriptChunk();
        }
    };

    autoNotesRecognition.onerror = (event) => {
        console.error('Speech recognition error:', event.error);
        if (event.error !== 'no-speech') {
            showNotification('Transcription error: ' + event.error, 'error');
        }
    };

    autoNotesRecognition.onend = () => {
        if (isAutoNotesActive) {
            autoNotesRecognition.start(); // Restart if still active
        }
    };

    autoNotesRecognition.start();
}

function stopLiveAutoNotes() {
    isAutoNotesActive = false;

    if (autoNotesRecognition) {
        autoNotesRecognition.stop();
    }

    if (processingInterval) {
        clearInterval(processingInterval);
        processingInterval = null;
    }

    if (fadeInterval) {
        clearInterval(fadeInterval);
        fadeInterval = null;
    }

    if (currentEventSource) {
        currentEventSource.close();
        currentEventSource = null;
    }

    // Update UI
    document.getElementById('startAutoNotesBtn').style.display = 'inline-block';
    document.getElementById('stopAutoNotesBtn').style.display = 'none';
    document.getElementById('autoNotesStatus').style.display = 'none';

    showNotification('Live Auto-Notes stopped', 'success');
}

function clearLiveAutoNotes() {
    transcriptBuffer = '';
    accumulatedNotes = [];
    document.getElementById('liveTranscriptText').innerHTML = '<p style="color: var(--text-secondary);">Click "Start Live Mode" to begin</p>';
    document.getElementById('importantNotesContainer').innerHTML = '<p style="color: var(--text-secondary); text-align: center; padding: 40px 0;">Important notes will appear here</p>';
}

// ============= Processing & Agent Integration =============

async function processTranscriptChunk() {
    if (!transcriptBuffer.trim() || transcriptBuffer.length < 20) {
        return; // Skip if buffer is too small
    }

    const chunk = transcriptBuffer.trim();
    const speaker = document.getElementById('autoNotesSpeaker').value || 'Unknown Speaker';
    const timestamp = new Date().toISOString();
    const session_id = window.currentSession?.id || '';

    // Clear buffer for next chunk
    transcriptBuffer = '';
    lastProcessedTime = Date.now();

    console.log(`📤 Sending transcript chunk (${chunk.length} chars) to backend...`);

    try {
        // Close any existing EventSource
        if (currentEventSource) {
            currentEventSource.close();
        }

        // Use EventSource for SSE streaming
        const response = await fetch('/api/live-auto-notes/process-stream', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                transcript_chunk: chunk,
                speaker: speaker,
                timestamp: timestamp,
                session_id: session_id
            })
        });

        if (!response.ok) {
            throw new Error(`HTTP ${response.status}`);
        }

        const reader = response.body.getReader();
        const decoder = new TextDecoder();

        while (true) {
            const { done, value } = await reader.read();
            if (done) break;

            const text = decoder.decode(value);
            const lines = text.split('\n');

            for (const line of lines) {
                if (line.startsWith('data: ')) {
                    const data = JSON.parse(line.substring(6));
                    handleStreamUpdate(data);
                }
            }
        }

    } catch (error) {
        console.error('Error processing transcript chunk:', error);
    }
}

function handleStreamUpdate(update) {
    const stage = update.stage;
    const message = update.message;
    const data = update.data;

    console.log(`📊 Stage: ${stage} - ${message}`);

    if (stage === 'complete' && data && data.note) {
        // Important note generated!
        const note = data.note;
        const importance = data.importance;

        if (importance >= IMPORTANCE_THRESHOLD) {
            displayImportantNote(note);
        }
    } else if (stage === 'skip') {
        console.log('⏭️ Chunk skipped (not important enough)');
    } else if (stage === 'error') {
        console.error('❌ Error:', update.error);
    }
}

// ============= UI Display & Animations =============

function displayImportantNote(note) {
    const container = document.getElementById('importantNotesContainer');

    // Remove placeholder if present
    if (container.querySelector('p')) {
        container.innerHTML = '';
    }

    // Create note card
    const card = document.createElement('div');
    card.className = 'note-card';

    // Format timestamp
    const time = new Date(note.timestamp);
    const timeStr = time.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit', second: '2-digit' });

    // Category badge color
    const categoryColors = {
        'key_decision': '#10b981',
        'country_position': '#3b82f6',
        'alliance_signal': '#8b5cf6',
        'strategic_move': '#f59e0b',
        'procedural': '#6b7280',
        'general': '#6b7280'
    };
    const badgeColor = categoryColors[note.category] || '#6b7280';

    card.innerHTML = `
        <div style="display: flex; justify-content: space-between; align-items: start; margin-bottom: 8px;">
            <span class="category-badge" style="background: ${badgeColor};">${note.category.replace('_', ' ').toUpperCase()}</span>
            <span class="note-timestamp">${timeStr}</span>
        </div>
        <h4 class="note-title">${note.title}</h4>
        <p class="note-content">${note.content}</p>
        <div class="note-meta">
            <span><strong>Speaker:</strong> ${note.speaker}</span>
            <div class="note-tags">
                ${note.tags.map(tag => `<span class="tag">${tag}</span>`).join('')}
            </div>
        </div>
    `;

    // Add to container at the top (newest first)
    container.insertBefore(card, container.firstChild);

    // Track note for fade management
    accumulatedNotes.push({
        element: card,
        timestamp: Date.now()
    });

    console.log(`✅ Displayed note: ${note.title}`);
}

function startFadeAnimation() {
    const container = document.getElementById('importantNotesContainer');
    const cards = container.querySelectorAll('.note-card:not(.note-fade)');

    if (cards.length === 0) return;

    console.log(`🌊 Fading ${cards.length} notes...`);

    // Apply fade animation to all current cards
    cards.forEach(card => {
        card.classList.add('note-fade');
    });

    // Remove cards after animation completes (2s)
    setTimeout(() => {
        clearOldNotes();
    }, 2000);
}

function clearOldNotes() {
    const container = document.getElementById('importantNotesContainer');
    const fadedCards = container.querySelectorAll('.note-fade');

    fadedCards.forEach(card => card.remove());

    // Reset accumulated notes
    accumulatedNotes = [];

    console.log('🗑️ Cleared old notes');

    // Show placeholder if empty
    if (container.children.length === 0) {
        container.innerHTML = '<p style="color: var(--text-secondary); text-align: center; padding: 40px 0;">Important notes will appear here</p>';
    }
}

// ============= Export Functions =============

async function exportAutoNotesToSession() {
    if (accumulatedNotes.length === 0) {
        showNotification('No notes to export', 'error');
        return;
    }

    if (!window.currentSession?.id) {
        showNotification('No active session. Please create or load a session first.', 'error');
        return;
    }

    try {
        // Compile all notes into a single note
        const notesText = accumulatedNotes.map(item => {
            const noteEl = item.element;
            const title = noteEl.querySelector('.note-title').textContent;
            const content = noteEl.querySelector('.note-content').textContent;
            const timestamp = noteEl.querySelector('.note-timestamp').textContent;
            return `### ${title} [${timestamp}]\n${content}\n`;
        }).join('\n');

        const noteData = {
            title: `Live Auto-Notes - ${new Date().toLocaleString()}`,
            content: notesText,
            folder: 'Live Sessions',
            session_id: window.currentSession.id
        };

        const response = await fetch('/api/notes', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(noteData)
        });

        if (response.ok) {
            showNotification(`Exported ${accumulatedNotes.length} notes to session`, 'success');
        } else {
            throw new Error('Failed to export notes');
        }
    } catch (error) {
        console.error('Error exporting notes:', error);
        showNotification('Failed to export notes', 'error');
    }
}
