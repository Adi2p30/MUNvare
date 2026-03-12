// Session Extensions - End MUN, Summaries, and Memory Import/Export

// ============= End Session Functionality =============

function endSessionConfirm(sessionId, event) {
    event.stopPropagation();

    if (!confirm('Are you sure you want to end this MUN session? This will generate a comprehensive summary and move it to Past MUNs.')) {
        return;
    }

    endSession(sessionId);
}

async function endSession(sessionId) {
    try {
        showNotification('Ending session and generating summary...', 'info');

        const response = await fetch(`${API_BASE}/sessions/${sessionId}/end`, {
            method: 'POST'
        });

        if (!response.ok) {
            throw new Error('Failed to end session');
        }

        const result = await response.json();

        showNotification('Session ended! Summary generated.', 'success');

        // Show summary modal
        showSummaryModal(result.summary, result.stats);

        // Reload sessions
        loadSessions();

        // If this was the current session, switch
        if (currentSession && currentSession.id === sessionId) {
            switchSession();
        }

    } catch (error) {
        console.error('Error ending session:', error);
        showNotification('Error ending session: ' + error.message, 'error');
    }
}

// ============= View Summary =============

function viewSessionSummary(sessionId, event) {
    event.stopPropagation();
    loadSessionSummary(sessionId);
}

async function loadSessionSummary(sessionId) {
    try {
        const response = await fetch(`${API_BASE}/sessions/${sessionId}/summary`);

        if (!response.ok) {
            throw new Error('Failed to load summary');
        }

        const result = await response.json();

        showSummaryModal(result.summary, null, result.session);

    } catch (error) {
        console.error('Error loading summary:', error);
        showNotification('Error loading summary: ' + error.message, 'error');
    }
}

function showSummaryModal(summary, stats, session) {
    const modal = document.getElementById('summaryModal');
    if (!modal) {
        createSummaryModal();
        return showSummaryModal(summary, stats, session);
    }

    const contentDiv = document.getElementById('summaryContent');

    let statsHtml = '';
    if (stats) {
        statsHtml = `
            <div style="display: flex; gap: 16px; margin-bottom: 24px; padding: 16px; background: var(--bg-tertiary); border-radius: 8px;">
                <div style="flex: 1; text-align: center;">
                    <div style="font-size: 28px; font-weight: bold; color: var(--accent);">${stats.notes_count}</div>
                    <div style="font-size: 12px; color: var(--text-secondary);">Notes Created</div>
                </div>
                <div style="flex: 1; text-align: center;">
                    <div style="font-size: 28px; font-weight: bold; color: var(--accent);">${stats.speeches_count}</div>
                    <div style="font-size: 12px; color: var(--text-secondary);">Speeches Given</div>
                </div>
                <div style="flex: 1; text-align: center;">
                    <div style="font-size: 28px; font-weight: bold; color: var(--accent);">${stats.chat_interactions}</div>
                    <div style="font-size: 12px; color: var(--text-secondary);">AI Interactions</div>
                </div>
            </div>
        `;
    }

    contentDiv.innerHTML = statsHtml + '<div class="markdown-content">' + marked.parse(summary) + '</div>';
    modal.style.display = 'flex';
}

function closeSummaryModal() {
    document.getElementById('summaryModal').style.display = 'none';
}

function createSummaryModal() {
    const modal = document.createElement('div');
    modal.id = 'summaryModal';
    modal.className = 'modal';
    modal.innerHTML = `
        <div class="modal-content" style="max-width: 900px; max-height: 90vh; overflow-y: auto;">
            <div class="modal-header">
                <h2>MUN Session Summary</h2>
                <button onclick="closeSummaryModal()" class="modal-close">&times;</button>
            </div>
            <div id="summaryContent" style="padding: 24px;"></div>
        </div>
    `;
    document.body.appendChild(modal);

    // Close on outside click
    modal.onclick = function(event) {
        if (event.target === modal) {
            closeSummaryModal();
        }
    };
}

// ============= Import Memory =============

function showImportModal(sourceSessionId, event) {
    event.stopPropagation();

    const modal = document.getElementById('importMemoryModal');
    if (!modal) {
        createImportModal();
        return showImportModal(sourceSessionId, event);
    }

    // Store source session ID
    document.getElementById('sourceSessionIdForImport').value = sourceSessionId;

    // Load active sessions
    loadActiveSessionsForImport();

    modal.style.display = 'flex';
}

function closeImportModal() {
    document.getElementById('importMemoryModal').style.display = 'none';
}

async function loadActiveSessionsForImport() {
    try {
        const response = await fetch(`${API_BASE}/sessions/active`);
        const sessions = await response.json();

        const container = document.getElementById('importTargetSessionsList');
        container.innerHTML = '';

        if (sessions.length === 0) {
            container.innerHTML = '<p style="color: var(--text-secondary);">No active sessions available. Create a new session first.</p>';
            return;
        }

        sessions.forEach(session => {
            const div = document.createElement('div');
            div.className = 'import-session-item';
            div.innerHTML = `
                <div>
                    <div style="font-weight: bold;">${session.name}</div>
                    <div style="font-size: 12px; color: var(--text-secondary);">${session.description || 'No description'}</div>
                </div>
                <button onclick="importToSession('${session.id}')" class="btn btn-primary btn-sm">Import Here</button>
            `;
            container.appendChild(div);
        });

    } catch (error) {
        console.error('Error loading sessions for import:', error);
        showNotification('Error loading sessions', 'error');
    }
}

async function importToSession(targetSessionId) {
    const sourceSessionId = document.getElementById('sourceSessionIdForImport').value;

    try {
        showNotification('Importing session memory...', 'info');

        const response = await fetch(`${API_BASE}/sessions/${targetSessionId}/import/${sourceSessionId}`, {
            method: 'POST'
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.error || 'Failed to import memory');
        }

        const result = await response.json();

        showNotification('Memory imported successfully!', 'success');
        closeImportModal();

        // Reload sessions
        loadSessions();

    } catch (error) {
        console.error('Error importing memory:', error);
        showNotification('Error importing memory: ' + error.message, 'error');
    }
}

function createImportModal() {
    const modal = document.createElement('div');
    modal.id = 'importMemoryModal';
    modal.className = 'modal';
    modal.innerHTML = `
        <div class="modal-content">
            <div class="modal-header">
                <h2>Import Session Memory</h2>
                <button onclick="closeImportModal()" class="modal-close">&times;</button>
            </div>
            <div style="padding: 24px;">
                <p style="margin-bottom: 16px; color: var(--text-secondary);">
                    Select which active session you want to import this knowledge into. The compressed memory and insights from this past MUN will be merged into the target session.
                </p>
                <input type="hidden" id="sourceSessionIdForImport" />
                <div id="importTargetSessionsList" style="display: flex; flex-direction: column; gap: 12px;"></div>
            </div>
        </div>
    `;
    document.body.appendChild(modal);

    modal.onclick = function(event) {
        if (event.target === modal) {
            closeImportModal();
        }
    };
}

// ============= Detach Memory =============

async function detachMemory(sessionId, sourceSessionId) {
    if (!confirm('Are you sure you want to detach this imported memory?')) {
        return;
    }

    try {
        const response = await fetch(`${API_BASE}/sessions/${sessionId}/detach/${sourceSessionId}`, {
            method: 'POST'
        });

        if (!response.ok) {
            throw new Error('Failed to detach memory');
        }

        showNotification('Memory detached successfully', 'success');
        loadSessions();

    } catch (error) {
        console.error('Error detaching memory:', error);
        showNotification('Error detaching memory: ' + error.message, 'error');
    }
}

// Add CSS for import session items
const style = document.createElement('style');
style.textContent = `
    .import-session-item {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 12px;
        background: var(--bg-tertiary);
        border: 1px solid var(--border);
        border-radius: 8px;
        transition: all 0.2s;
    }

    .import-session-item:hover {
        border-color: var(--accent);
        background: var(--bg-secondary);
    }

    .btn-sm {
        padding: 6px 12px;
        font-size: 13px;
    }
`;
document.head.appendChild(style);

console.log('✅ Session extensions loaded: End Session, Summaries, Import/Export');
