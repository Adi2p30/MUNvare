// Notes Extensions - Export and Voice-to-Text functionality

// ============= EXPORT FUNCTIONALITY =============

function exportNotePDF(noteId) {
    window.open(`${API_BASE}/notes/${noteId}/export/pdf`, '_blank');
    showNotification('Downloading PDF...', 'success');
}

function exportNoteTXT(noteId) {
    window.open(`${API_BASE}/notes/${noteId}/export/txt`, '_blank');
    showNotification('Downloading TXT...', 'success');
}

function exportAllNotesTXT() {
    window.open(`${API_BASE}/notes/export-all/txt`, '_blank');
    showNotification('Downloading all notes as TXT...', 'success');
}

// ============= VOICE-TO-TEXT FOR NOTES =============

let voiceRecognition = null;
let isRecording = false;
let currentNoteTextarea = null;

function initializeVoiceRecognition() {
    // Check if browser supports speech recognition
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;

    if (!SpeechRecognition) {
        console.warn('Speech recognition not supported in this browser');
        return null;
    }

    const recognition = new SpeechRecognition();
    recognition.continuous = true;
    recognition.interimResults = true;
    recognition.lang = 'en-US';

    let finalTranscript = '';
    let interimTranscript = '';

    recognition.onstart = function() {
        isRecording = true;
        updateRecordingUI(true);
        showNotification('Recording started - speak now', 'info');
    };

    recognition.onresult = function(event) {
        interimTranscript = '';

        for (let i = event.resultIndex; i < event.results.length; i++) {
            const transcript = event.results[i][0].transcript;

            if (event.results[i].isFinal) {
                finalTranscript += transcript + ' ';
            } else {
                interimTranscript += transcript;
            }
        }

        // Update the textarea with transcribed text
        if (currentNoteTextarea) {
            const cursorPos = currentNoteTextarea.selectionStart;
            const textBefore = currentNoteTextarea.value.substring(0, cursorPos);
            const textAfter = currentNoteTextarea.value.substring(cursorPos);

            // Show interim results in a preview
            updateInterimPreview(interimTranscript);

            // Only update when we have final results
            if (finalTranscript) {
                currentNoteTextarea.value = textBefore + finalTranscript + textAfter;
                currentNoteTextarea.selectionStart = cursorPos + finalTranscript.length;
                currentNoteTextarea.selectionEnd = cursorPos + finalTranscript.length;
                finalTranscript = '';
            }
        }
    };

    recognition.onerror = function(event) {
        console.error('Speech recognition error:', event.error);
        isRecording = false;
        updateRecordingUI(false);

        if (event.error === 'no-speech') {
            showNotification('No speech detected. Try again.', 'warning');
        } else if (event.error === 'not-allowed') {
            showNotification('Microphone access denied. Please enable microphone permissions.', 'error');
        } else {
            showNotification('Error: ' + event.error, 'error');
        }
    };

    recognition.onend = function() {
        isRecording = false;
        updateRecordingUI(false);
        hideInterimPreview();
    };

    return recognition;
}

function toggleVoiceRecording(textareaId) {
    currentNoteTextarea = document.getElementById(textareaId);

    if (!currentNoteTextarea) {
        showNotification('Note textarea not found', 'error');
        return;
    }

    if (!voiceRecognition) {
        voiceRecognition = initializeVoiceRecognition();

        if (!voiceRecognition) {
            showNotification('Voice recognition not supported in this browser. Try Chrome or Edge.', 'error');
            return;
        }
    }

    if (isRecording) {
        voiceRecognition.stop();
        showNotification('Recording stopped', 'info');
    } else {
        try {
            voiceRecognition.start();
        } catch (error) {
            console.error('Error starting recognition:', error);
            showNotification('Could not start recording. Please try again.', 'error');
        }
    }
}

function updateRecordingUI(recording) {
    const buttons = document.querySelectorAll('.voice-record-btn');

    buttons.forEach(btn => {
        if (recording) {
            btn.classList.add('recording');
            btn.innerHTML = `
                <svg class="icon icon-sm recording-icon" fill="currentColor" stroke="none" viewBox="0 0 24 24">
                    <rect x="6" y="6" width="12" height="12" rx="2"/>
                </svg>
                <span>Stop</span>
            `;
            btn.style.background = 'var(--danger)';
        } else {
            btn.classList.remove('recording');
            btn.innerHTML = `
                <svg class="icon icon-sm" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3z"/>
                </svg>
                <span>Voice</span>
            `;
            btn.style.background = '';
        }
    });
}

function updateInterimPreview(text) {
    let preview = document.getElementById('voiceInterimPreview');

    if (!preview) {
        preview = document.createElement('div');
        preview.id = 'voiceInterimPreview';
        preview.style.cssText = `
            position: fixed;
            bottom: 80px;
            right: 20px;
            background: var(--bg-tertiary);
            border: 2px solid var(--accent);
            border-radius: 8px;
            padding: 12px 16px;
            max-width: 400px;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
            z-index: 1000;
            font-size: 14px;
            color: var(--text-secondary);
            font-style: italic;
        `;
        document.body.appendChild(preview);
    }

    preview.textContent = text || 'Listening...';
}

function hideInterimPreview() {
    const preview = document.getElementById('voiceInterimPreview');
    if (preview) {
        preview.remove();
    }
}

// ============= ADD EXPORT/VOICE BUTTONS TO NOTES =============

function addExportButtonsToNote(noteCard, noteId) {
    const actionsDiv = noteCard.querySelector('.note-card-actions');
    if (!actionsDiv) return;

    // Add export dropdown
    const exportBtn = document.createElement('div');
    exportBtn.className = 'export-dropdown';
    exportBtn.innerHTML = `
        <button class="btn btn-secondary btn-sm" onclick="toggleExportMenu('${noteId}')" style="display: flex; align-items: center; gap: 4px;">
            <svg class="icon icon-sm" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"/>
            </svg>
            Export
        </button>
        <div class="export-menu" id="exportMenu-${noteId}" style="display: none;">
            <button onclick="exportNotePDF('${noteId}'); toggleExportMenu('${noteId}')" class="export-menu-item">
                <svg class="icon icon-sm" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 21h10a2 2 0 002-2V9.414a1 1 0 00-.293-.707l-5.414-5.414A1 1 0 0012.586 3H7a2 2 0 00-2 2v14a2 2 0 002 2z"/>
                </svg>
                Export as PDF
            </button>
            <button onclick="exportNoteTXT('${noteId}'); toggleExportMenu('${noteId}')" class="export-menu-item">
                <svg class="icon icon-sm" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"/>
                </svg>
                Export as TXT
            </button>
        </div>
    `;

    actionsDiv.insertBefore(exportBtn, actionsDiv.firstChild);
}

function toggleExportMenu(noteId) {
    const menu = document.getElementById(`exportMenu-${noteId}`);
    if (menu) {
        menu.style.display = menu.style.display === 'none' ? 'block' : 'none';
    }

    // Close other menus
    document.querySelectorAll('.export-menu').forEach(m => {
        if (m.id !== `exportMenu-${noteId}`) {
            m.style.display = 'none';
        }
    });
}

// Close export menus when clicking outside
document.addEventListener('click', function(event) {
    if (!event.target.closest('.export-dropdown')) {
        document.querySelectorAll('.export-menu').forEach(m => {
            m.style.display = 'none';
        });
    }
});

// Add voice button to note editor
function addVoiceButtonToEditor() {
    const noteContent = document.getElementById('noteContent');
    if (!noteContent) return;

    // Check if button already exists
    if (document.querySelector('.voice-record-btn')) return;

    const voiceBtn = document.createElement('button');
    voiceBtn.className = 'voice-record-btn btn btn-secondary';
    voiceBtn.type = 'button';
    voiceBtn.onclick = () => toggleVoiceRecording('noteContent');
    voiceBtn.innerHTML = `
        <svg class="icon icon-sm" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3z"/>
        </svg>
        <span>Voice</span>
    `;
    voiceBtn.style.cssText = 'display: flex; align-items: center; gap: 6px; margin-right: 8px;';

    // Add to note modal
    const saveBtn = document.querySelector('#noteModal button[onclick*="saveNote"]');
    if (saveBtn) {
        saveBtn.parentElement.insertBefore(voiceBtn, saveBtn);
    }
}

// Add export all button to notes toolbar
function addExportAllButton() {
    const notesSection = document.getElementById('notes');
    if (!notesSection) return;

    // Check if button already exists
    if (document.getElementById('exportAllNotesBtn')) return;

    const toolbar = notesSection.querySelector('h2')?.parentElement;
    if (!toolbar) return;

    const exportAllBtn = document.createElement('button');
    exportAllBtn.id = 'exportAllNotesBtn';
    exportAllBtn.className = 'btn btn-secondary';
    exportAllBtn.onclick = exportAllNotesTXT;
    exportAllBtn.innerHTML = `
        <svg class="icon icon-sm" fill="none" stroke="currentColor" viewBox="0 0 24 24" style="display: inline-block; vertical-align: middle; margin-right: 4px;">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"/>
        </svg>
        Export All Notes
    `;
    exportAllBtn.style.cssText = 'margin-left: auto;';

    const h2 = notesSection.querySelector('h2');
    if (h2 && h2.parentElement) {
        h2.parentElement.style.display = 'flex';
        h2.parentElement.style.alignItems = 'center';
        h2.parentElement.style.gap = '12px';
        h2.parentElement.appendChild(exportAllBtn);
    }
}

// Add export menu to note sidebar items
function addExportToNoteSidebar(noteItem, noteId) {
    if (!noteItem || noteItem.querySelector('.note-export-btn')) return;

    const exportBtn = document.createElement('button');
    exportBtn.className = 'note-export-btn';
    exportBtn.onclick = (e) => {
        e.stopPropagation();
        showNoteExportOptions(noteId, e);
    };
    exportBtn.innerHTML = `
        <svg class="icon icon-sm" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 10v6m0 0l-3-3m3 3l3-3"/>
        </svg>
    `;
    exportBtn.title = 'Export note';
    exportBtn.style.cssText = `
        position: absolute;
        right: 40px;
        top: 50%;
        transform: translateY(-50%);
        background: none;
        border: none;
        color: var(--text-secondary);
        cursor: pointer;
        padding: 4px;
        display: none;
    `;

    noteItem.style.position = 'relative';
    noteItem.appendChild(exportBtn);

    // Show on hover
    noteItem.addEventListener('mouseenter', () => {
        exportBtn.style.display = 'block';
    });
    noteItem.addEventListener('mouseleave', () => {
        exportBtn.style.display = 'none';
    });
}

function showNoteExportOptions(noteId, event) {
    event.stopPropagation();

    // Remove existing menu
    const existingMenu = document.querySelector('.quick-export-menu');
    if (existingMenu) existingMenu.remove();

    const menu = document.createElement('div');
    menu.className = 'quick-export-menu';
    menu.style.cssText = `
        position: fixed;
        left: ${event.clientX}px;
        top: ${event.clientY}px;
        background: var(--bg-secondary);
        border: 1px solid var(--border);
        border-radius: 8px;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
        min-width: 150px;
        z-index: 10000;
        overflow: hidden;
    `;

    menu.innerHTML = `
        <button onclick="exportNotePDF('${noteId}'); this.closest('.quick-export-menu').remove();" class="export-menu-item">
            <svg class="icon icon-sm" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 21h10a2 2 0 002-2V9.414a1 1 0 00-.293-.707l-5.414-5.414A1 1 0 0012.586 3H7a2 2 0 00-2 2v14a2 2 0 002 2z"/>
            </svg>
            PDF
        </button>
        <button onclick="exportNoteTXT('${noteId}'); this.closest('.quick-export-menu').remove();" class="export-menu-item">
            <svg class="icon icon-sm" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"/>
            </svg>
            TXT
        </button>
    `;

    document.body.appendChild(menu);

    // Close on click outside
    setTimeout(() => {
        document.addEventListener('click', function closeMenu() {
            menu.remove();
            document.removeEventListener('click', closeMenu);
        });
    }, 100);
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', function() {
    // Add voice button when note modal is shown
    const noteModal = document.getElementById('noteModal');
    if (noteModal) {
        const observer = new MutationObserver(function(mutations) {
            mutations.forEach(function(mutation) {
                if (mutation.attributeName === 'style' && noteModal.style.display === 'flex') {
                    setTimeout(addVoiceButtonToEditor, 100);
                }
            });
        });
        observer.observe(noteModal, { attributes: true });
    }

    // Add export all button
    setTimeout(addExportAllButton, 500);

    // Add export buttons to note items in sidebar
    const observer = new MutationObserver(function() {
        document.querySelectorAll('.note-item').forEach(item => {
            const noteId = item.dataset.noteId;
            if (noteId && !item.querySelector('.note-export-btn')) {
                addExportToNoteSidebar(item, noteId);
            }
        });
    });

    const notesList = document.getElementById('notesList');
    if (notesList) {
        observer.observe(notesList, { childList: true, subtree: true });
    }
});

// Add CSS for export menu and voice button
const style = document.createElement('style');
style.textContent = `
    .export-dropdown {
        position: relative;
        display: inline-block;
    }

    .export-menu {
        position: absolute;
        top: 100%;
        left: 0;
        margin-top: 4px;
        background: var(--bg-secondary);
        border: 1px solid var(--border);
        border-radius: 8px;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
        min-width: 180px;
        z-index: 1000;
        overflow: hidden;
    }

    .export-menu-item {
        width: 100%;
        padding: 10px 16px;
        border: none;
        background: none;
        color: var(--text-primary);
        font-size: 14px;
        text-align: left;
        cursor: pointer;
        display: flex;
        align-items: center;
        gap: 8px;
        transition: background 0.2s;
    }

    .export-menu-item:hover {
        background: var(--bg-tertiary);
    }

    .export-menu-item svg {
        width: 18px;
        height: 18px;
    }

    .voice-record-btn {
        transition: all 0.3s ease;
    }

    .voice-record-btn.recording {
        animation: pulse 1.5s infinite;
        box-shadow: 0 0 0 0 rgba(239, 68, 68, 0.7);
    }

    @keyframes pulse {
        0% {
            box-shadow: 0 0 0 0 rgba(239, 68, 68, 0.7);
        }
        70% {
            box-shadow: 0 0 0 10px rgba(239, 68, 68, 0);
        }
        100% {
            box-shadow: 0 0 0 0 rgba(239, 68, 68, 0);
        }
    }

    .recording-icon {
        animation: blink 1s infinite;
    }

    @keyframes blink {
        0%, 50% {
            opacity: 1;
        }
        51%, 100% {
            opacity: 0.3;
        }
    }
`;
document.head.appendChild(style);

console.log('✅ Notes extensions loaded: Export (PDF/TXT) and Voice-to-Text');
