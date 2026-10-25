// Session Management JavaScript

// Global state for current session
let currentSession = null;
window.currentSession = currentSession;

// ============= Session Management Functions =============

document.addEventListener('DOMContentLoaded', function() {
    // Load sessions on start
    loadSessions();
});

async function loadSessions() {
    try {
        // Load active and ended sessions separately
        const activeResponse = await fetch(`${API_BASE}/sessions/active`);
        const activeSessions = await activeResponse.json();

        const endedResponse = await fetch(`${API_BASE}/sessions/ended`);
        const endedSessions = await endedResponse.json();

        const container = document.getElementById('sessionsList');
        container.innerHTML = '';

        // Active Sessions Section
        if (activeSessions.length > 0) {
            const activeHeader = document.createElement('h3');
            activeHeader.textContent = 'Active Sessions';
            activeHeader.style.cssText = 'grid-column: 1 / -1; margin-bottom: 12px; color: var(--accent);';
            container.appendChild(activeHeader);

            activeSessions.forEach(session => {
                const card = createActiveSessionCard(session);
                container.appendChild(card);
            });
        }

        // Past MUNs Section
        if (endedSessions.length > 0) {
            const endedHeader = document.createElement('h3');
            endedHeader.textContent = 'Past MUNs';
            endedHeader.style.cssText = 'grid-column: 1 / -1; margin: 24px 0 12px 0; color: var(--text-secondary);';
            container.appendChild(endedHeader);

            endedSessions.forEach(session => {
                const card = createPastSessionCard(session);
                container.appendChild(card);
            });
        }

        if (activeSessions.length === 0 && endedSessions.length === 0) {
            container.innerHTML = `
                <div style="text-align: center; padding: 40px; color: var(--text-secondary); grid-column: 1 / -1;">
                    <p style="font-size: 16px; margin-bottom: 8px;">No MUN sessions yet</p>
                    <p style="font-size: 14px;">Click the button below to create your first session</p>
                </div>
            `;
        }

    } catch (error) {
        console.error('Error loading sessions:', error);
        showNotification('Error loading sessions', 'error');
    }
}

function createActiveSessionCard(session) {
    const card = document.createElement('div');
    card.className = 'session-card';

    const lastAccessed = new Date(session.last_accessed);
    const dateStr = lastAccessed.toLocaleDateString('en-US', {
        month: 'short',
        day: 'numeric',
        year: 'numeric'
    });

    const statusBadge = '<span style="background: var(--success); color: white; padding: 2px 8px; border-radius: 4px; font-size: 11px; font-weight: bold;">ACTIVE</span>';

    card.innerHTML = `
        <div class="session-card-header">
            <div>
                <h3>${session.name} ${statusBadge}</h3>
            </div>
            <div class="session-card-actions">
                <button onclick="endSessionConfirm('${session.id}', event)" class="btn-icon" title="End MUN session" style="color: var(--accent);">
                    <svg class="icon icon-sm" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"/></svg>
                </button>
                <button onclick="editSessionModal('${session.id}', event)" class="btn-icon" title="Edit session">
                    <svg class="icon icon-sm" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z"/></svg>
                </button>
                <button onclick="deleteSessionConfirm('${session.id}', event)" class="btn-icon" title="Delete session">
                    <svg class="icon icon-sm" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"/></svg>
                </button>
            </div>
        </div>
        <p class="session-description">${session.description || 'No description'}</p>
        <div class="session-meta">
            <span><svg class="icon icon-sm" fill="none" stroke="currentColor" viewBox="0 0 24 24" style="display: inline-block; vertical-align: middle; margin-right: 4px;"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z"/></svg> ${session.dates || 'No dates set'}</span>
            <span style="color: var(--text-secondary); font-size: 12px;">Last accessed: ${dateStr}</span>
        </div>
    `;

    card.onclick = (e) => {
        if (e.target.classList.contains('btn') || e.target.classList.contains('btn-icon') || e.target.closest('.btn') || e.target.closest('.btn-icon')) {
            return;
        }
        selectSession(session.id);
    };

    return card;
}

function createPastSessionCard(session) {
    const card = document.createElement('div');
    card.className = 'session-card';
    card.style.opacity = '0.85';
    card.style.border = '1px solid var(--border)';

    const endedAt = new Date(session.ended_at);
    const dateStr = endedAt.toLocaleDateString('en-US', {
        month: 'short',
        day: 'numeric',
        year: 'numeric'
    });

    const statusBadge = '<span style="background: var(--text-secondary); color: white; padding: 2px 8px; border-radius: 4px; font-size: 11px;">ENDED</span>';

    card.innerHTML = `
        <div class="session-card-header">
            <div>
                <h3>${session.name} ${statusBadge}</h3>
            </div>
            <div class="session-card-actions" style="display: flex; gap: 8px; align-items: center;">
                <button onclick="viewSessionSummary('${session.id}', event)" class="btn btn-secondary btn-sm" title="View summary" style="display: flex; align-items: center; gap: 4px; padding: 6px 12px; font-size: 13px;">
                    <svg class="icon icon-sm" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"/></svg>
                    Summary
                </button>
                <button onclick="showImportModal('${session.id}', event)" class="btn btn-primary btn-sm" title="Import to session" style="display: flex; align-items: center; gap: 4px; padding: 6px 12px; font-size: 13px;">
                    <svg class="icon icon-sm" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12"/></svg>
                    Import
                </button>
            </div>
        </div>
        <p class="session-description">${session.description || 'No description'}</p>
        <div class="session-meta">
            <span><svg class="icon icon-sm" fill="none" stroke="currentColor" viewBox="0 0 24 24" style="display: inline-block; vertical-align: middle; margin-right: 4px;"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z"/></svg> ${session.dates || 'No dates set'}</span>
            <span style="color: var(--text-secondary); font-size: 12px;">Ended: ${dateStr}</span>
        </div>
    `;

    return card;
}

async function selectSession(sessionId) {
    try {
        const response = await fetch(`${API_BASE}/sessions/${sessionId}`);
        const session = await response.json();

        // Store current session
        currentSession = session;
        window.currentSession = currentSession;
        localStorage.setItem('currentSessionId', sessionId);
        localStorage.setItem('currentSessionName', session.name);

        // Update UI
        document.getElementById('currentSessionName').textContent = session.name;
        document.getElementById('currentSessionDisplay').style.display = 'block';
        document.getElementById('switchSessionBtn').style.display = 'block';

        // Navigate to dashboard
        navigateTo('dashboard');

        showNotification(`Loaded session: ${session.name}`, 'success');

        // Reload all data for this session
        loadNotes();
        loadSavedSpeeches();
        loadChatHistory();

    } catch (error) {
        console.error('Error selecting session:', error);
        showNotification('Error loading session', 'error');
    }
}

function switchSession() {
    // Clear current session
    currentSession = null;
    window.currentSession = currentSession;
    localStorage.removeItem('currentSessionId');

    // Hide session display
    document.getElementById('currentSessionDisplay').style.display = 'none';
    document.getElementById('switchSessionBtn').style.display = 'none';

    // Navigate back to start screen
    navigateTo('start-screen');

    // Reload sessions
    loadSessions();
}

function showCreateSessionModal() {
    document.getElementById('createSessionModal').style.display = 'flex';
    document.getElementById('newSessionName').focus();
}

function closeCreateSessionModal() {
    document.getElementById('createSessionModal').style.display = 'none';
    document.getElementById('newSessionName').value = '';
    document.getElementById('newSessionDescription').value = '';
    document.getElementById('newSessionDates').value = '';
}

async function createSession() {
    const name = document.getElementById('newSessionName').value.trim();
    const description = document.getElementById('newSessionDescription').value.trim();
    const dates = document.getElementById('newSessionDates').value.trim();

    if (!name) {
        showNotification('Please enter a session name', 'error');
        return;
    }

    try {
        const response = await fetch(`${API_BASE}/sessions`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ name, description, dates })
        });

        if (!response.ok) {
            throw new Error('Failed to create session');
        }

        const session = await response.json();

        showNotification('Session created successfully!', 'success');
        closeCreateSessionModal();

        // Automatically select the new session
        selectSession(session.id);

    } catch (error) {
        console.error('Error creating session:', error);
        showNotification('Error creating session', 'error');
    }
}

function deleteSessionConfirm(sessionId, event) {
    event.stopPropagation();

    if (!confirm('Are you sure you want to delete this session? All data will be permanently lost.')) {
        return;
    }

    deleteSessionById(sessionId);
}

async function deleteSessionById(sessionId) {
    try {
        const response = await fetch(`${API_BASE}/sessions/${sessionId}`, {
            method: 'DELETE'
        });

        if (!response.ok) {
            throw new Error('Failed to delete session');
        }

        showNotification('Session deleted', 'success');

        // If this was the current session, clear it
        if (currentSession && currentSession.id === sessionId) {
            switchSession();
        } else {
            loadSessions();
        }

    } catch (error) {
        console.error('Error deleting session:', error);
        showNotification('Error deleting session', 'error');
    }
}

function editSessionModal(sessionId, event) {
    event.stopPropagation();

    // Find the session data
    fetch(`${API_BASE}/sessions/${sessionId}`)
        .then(response => response.json())
        .then(session => {
            document.getElementById('editSessionId').value = session.id;
            document.getElementById('editSessionName').value = session.name;
            document.getElementById('editSessionDescription').value = session.description || '';
            document.getElementById('editSessionDates').value = session.dates || '';
            document.getElementById('editSessionModal').style.display = 'flex';
        })
        .catch(error => {
            console.error('Error loading session for edit:', error);
            showNotification('Error loading session', 'error');
        });
}

function closeEditSessionModal() {
    document.getElementById('editSessionModal').style.display = 'none';
}

async function updateSession() {
    const sessionId = document.getElementById('editSessionId').value;
    const name = document.getElementById('editSessionName').value.trim();
    const description = document.getElementById('editSessionDescription').value.trim();
    const dates = document.getElementById('editSessionDates').value.trim();

    if (!name) {
        showNotification('Please enter a session name', 'error');
        return;
    }

    try {
        const response = await fetch(`${API_BASE}/sessions/${sessionId}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ name, description, dates })
        });

        if (!response.ok) {
            throw new Error('Failed to update session');
        }

        showNotification('Session updated successfully!', 'success');
        closeEditSessionModal();

        // Reload sessions
        loadSessions();

        // If this is the current session, update the display
        if (currentSession && currentSession.id === sessionId) {
            currentSession.name = name;
            currentSession.description = description;
            currentSession.dates = dates;
            document.getElementById('currentSessionName').textContent = name;
            localStorage.setItem('currentSessionName', name);
        }

    } catch (error) {
        console.error('Error updating session:', error);
        showNotification('Error updating session', 'error');
    }
}

// Check if there's a saved session on page load
window.addEventListener('DOMContentLoaded', function() {
    const savedSessionId = localStorage.getItem('currentSessionId');
    if (savedSessionId) {
        // Try to load the saved session
        selectSession(savedSessionId).catch(() => {
            // If loading fails, clear and show start screen
            localStorage.removeItem('currentSessionId');
            localStorage.removeItem('currentSessionName');
        });
    }
});

// Attach the active session to /api/ requests. Guard so a second load does not wrap twice.
if (!window.__sessionFetchWrapped) {
    window.__sessionFetchWrapped = true;
    const originalFetch = window.fetch.bind(window);
    window.fetch = function(input, init) {
        if (typeof input === 'string' && input.includes('/api/') && currentSession && currentSession.id != null) {
            const headers = new Headers(init && init.headers);
            if (!headers.has('X-Session-Id')) {
                headers.set('X-Session-Id', String(currentSession.id));
                init = Object.assign({}, init, { headers: headers });
            }
        }
        return originalFetch(input, init);
    };
}
