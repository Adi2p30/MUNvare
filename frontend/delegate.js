// MUNvare Delegate Interface
const socket = io();
let roomCode = null;
let country = null;
let state = null;
let hasVoted = false;

// === JOIN ===
function joinRoom() {
    const code = document.getElementById('room-code-input').value.trim().toUpperCase();
    const countryName = document.getElementById('country-input').value.trim();
    if (!code || !countryName) { alert('Enter room code and country name'); return; }
    roomCode = code;
    country = countryName;
    localStorage.setItem('delegateRoom', roomCode);
    localStorage.setItem('delegateCountry', country);
    socket.emit('join_room', { room_code: roomCode, country, role: 'delegate' });
}

socket.on('joined', (data) => {
    document.getElementById('join-screen').style.display = 'none';
    document.getElementById('main-view').style.display = 'flex';
    document.getElementById('my-country').textContent = country;
    document.getElementById('room-code-badge').textContent = roomCode;
});

socket.on('room_state_updated', (newState) => {
    state = newState;
    renderAll();
});

socket.on('room_state', (newState) => {
    state = newState;
    renderAll();
});

socket.on('voting_started', () => { hasVoted = false; renderVotingActions(); });
socket.on('voting_ended', () => { hasVoted = false; });

socket.on('error', (data) => {
    showToast(data.message, 'error');
});

socket.on('announcement', (data) => {
    showToast('📢 ' + data.message, 'info');
});

// === HELPERS ===
function delegateEmit(event, data = {}) {
    socket.emit(event, { ...data, room_code: roomCode, country });
}

function showToast(message, type = 'info') {
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    toast.textContent = message;
    document.getElementById('toast-container').appendChild(toast);
    setTimeout(() => toast.remove(), 4000);
}

function formatTime(seconds) {
    if (isNaN(seconds) || seconds < 0) seconds = 0;
    const m = Math.floor(seconds / 60);
    const s = Math.floor(seconds % 60);
    return `${m}:${s.toString().padStart(2, '0')}`;
}

function handleOverlayClick(event, modalId) {
    if (event.target === event.currentTarget) {
        closeModal(modalId);
    }
}

// === ACTIONS ===
function requestToSpeak() {
    const context = state?.status === 'mod_caucus' ? 'mod_caucus' : 'gsl';
    delegateEmit('request_to_speak', { context });
    showToast('Added to speakers list', 'success');
}

function withdrawFromList() {
    delegateEmit('withdraw_from_list');
    showToast('Withdrawn from speakers list', 'info');
}

function proposeMotion() {
    const modal = document.getElementById('motion-modal');
    modal.style.display = 'flex';
}

function submitMotion() {
    const type = document.getElementById('motion-type').value;
    const details = {};
    if (type === 'mod_caucus') {
        details.topic = document.getElementById('motion-topic').value;
        details.total_time = parseInt(document.getElementById('motion-total-time').value) || 300;
        details.speaker_time = parseInt(document.getElementById('motion-speaker-time').value) || 60;
    } else if (type === 'unmod_caucus') {
        details.duration = parseInt(document.getElementById('motion-duration').value) || 300;
        details.purpose = document.getElementById('motion-purpose').value;
    }
    delegateEmit('propose_motion', { type, details });
    closeModal('motion-modal');
    showToast('Motion proposed', 'success');
}

function raisePoint() {
    const modal = document.getElementById('point-modal');
    modal.style.display = 'flex';
}

function submitPoint() {
    const type = document.getElementById('point-type').value;
    const details = document.getElementById('point-details').value;
    delegateEmit('raise_point', { type, details });
    closeModal('point-modal');
    showToast('Point raised', 'success');
}

function castVote(vote) {
    if (hasVoted) { showToast('You have already voted', 'error'); return; }
    delegateEmit('cast_vote', { vote });
    hasVoted = true;
    showToast(`Vote cast: ${vote}`, 'success');
    renderVotingActions();
}

function requestRightOfReply() {
    const regarding = prompt('Regarding (which country/statement):');
    if (!regarding) return;
    delegateEmit('request_right_of_reply', { regarding });
    showToast('Right of reply requested', 'success');
}

function submitWorkingPaper() {
    const modal = document.getElementById('wp-modal');
    modal.style.display = 'flex';
}

function submitWP() {
    const title = document.getElementById('wp-title').value.trim();
    const sponsors = document.getElementById('wp-sponsors').value.split(',').map(s => s.trim()).filter(Boolean);
    const signatories = document.getElementById('wp-signatories').value.split(',').map(s => s.trim()).filter(Boolean);
    const content = document.getElementById('wp-content').value;
    if (!title) { alert('Enter title'); return; }
    delegateEmit('submit_working_paper', { title, sponsors, signatories, content });
    closeModal('wp-modal');
    showToast('Working paper submitted', 'success');
}

function closeModal(id) { document.getElementById(id).style.display = 'none'; }

// === RENDER ===
function renderAll() {
    if (!state) return;
    renderStatus();
    renderCurrentActivity();
    renderActions();
    renderSpeakerList();
    renderAnnouncements();
    renderDocuments();
}

function renderStatus() {
    const statusEl = document.getElementById('committee-status');
    if (statusEl) {
        statusEl.textContent = (state.status || 'unknown').replace('_', ' ').toUpperCase();
        statusEl.className = 'status-badge status-' + state.status;
    }
    // Update committee name if provided
    if (state.committee_name) {
        const nameEl = document.getElementById('committee-name');
        if (nameEl) nameEl.textContent = state.committee_name;
    }
    renderTimer();
}

let timerInterval = null;
function renderTimer() {
    if (timerInterval) clearInterval(timerInterval);
    const timerEl = document.getElementById('main-timer');
    if (!timerEl) return;

    function updateTimerDisplay() {
        if (!state) return;
        let timer = null;
        let label = '';

        if (state.status === 'gsl' && state.gsl.timer.running) {
            timer = state.gsl.timer;
            label = 'Speaker Time';
        } else if (state.status === 'mod_caucus') {
            if (state.mod_caucus.speaker_timer.running) {
                timer = state.mod_caucus.speaker_timer;
                label = 'Speaker';
            } else if (state.mod_caucus.timer.running) {
                timer = state.mod_caucus.timer;
                label = 'Total Caucus';
            }
        } else if (state.status === 'unmod_caucus' && state.unmod_caucus.timer.running) {
            timer = state.unmod_caucus.timer;
            label = 'Unmod Caucus';
        }

        if (timer) {
            const elapsed = timer.started_at ? (Date.now() / 1000) - timer.started_at : 0;
            const remaining = Math.max(0, timer.remaining - elapsed);
            timerEl.innerHTML = `<div class="timer-label">${label}</div><div class="timer-value">${formatTime(Math.floor(remaining))}</div>`;
        } else {
            timerEl.innerHTML = `<div class="timer-label">${(state.status || '').replace('_', ' ')}</div>`;
        }
    }

    updateTimerDisplay();
    timerInterval = setInterval(updateTimerDisplay, 100);
}

function renderCurrentActivity() {
    const el = document.getElementById('current-activity');
    if (!el || !state) return;

    let content = '';
    switch (state.status) {
        case 'gsl':
            const currentSpeaker = state.gsl.speakers[state.gsl.current_index];
            content = `
                <div class="activity-header">General Speakers List</div>
                ${currentSpeaker ? `<div class="current-speaker">🎤 ${currentSpeaker}</div>` : '<div class="no-speaker">No current speaker</div>'}
                <div class="my-position">${getMyPosition()}</div>
            `;
            break;
        case 'mod_caucus':
            const mcSpeaker = state.mod_caucus.speakers[state.mod_caucus.current_index];
            content = `
                <div class="activity-header">Moderated Caucus</div>
                <div class="caucus-topic">${state.mod_caucus.topic}</div>
                ${mcSpeaker ? `<div class="current-speaker">🎤 ${mcSpeaker}</div>` : '<div class="no-speaker">No current speaker</div>'}
            `;
            break;
        case 'unmod_caucus':
            content = `
                <div class="activity-header">Unmoderated Caucus</div>
                <div class="caucus-topic">${state.unmod_caucus.purpose}</div>
                <div class="unmod-note">Delegates may move freely</div>
            `;
            break;
        case 'voting':
            content = `
                <div class="activity-header">Voting Procedure</div>
                <div class="voting-motion">${state.voting.motion}</div>
                <div class="voting-type">${state.voting.type} vote</div>
            `;
            break;
        case 'roll_call':
            const myDelegate = state.delegates.find(d => d.country === country);
            content = `
                <div class="activity-header">Roll Call</div>
                <div class="attendance-status ${myDelegate?.present ? 'present' : 'absent'}">
                    You are marked: ${myDelegate?.present ? 'Present' : 'Absent'}
                </div>
            `;
            break;
        case 'suspended':
            content = '<div class="activity-header">Session Suspended</div>';
            break;
        case 'adjourned':
            content = '<div class="activity-header">Session Adjourned</div>';
            break;
        default:
            content = `<div class="activity-header">${state.status}</div>`;
    }
    el.innerHTML = content;
}

function getMyPosition() {
    if (!state || !country) return '';
    const pos = state.gsl.speakers.indexOf(country);
    if (pos === -1) return '';
    if (pos === state.gsl.current_index) return '🎤 You are speaking now!';
    if (pos < state.gsl.current_index) return '✓ You have spoken';
    return `You are #${pos + 1} in the queue`;
}

function renderActions() {
    renderVotingActions();
    if (!state) return;
    const votingActive = state.voting?.active;
    document.getElementById('speak-actions').style.display = votingActive ? 'none' : 'block';
    document.getElementById('voting-actions').style.display = votingActive ? 'block' : 'none';
}

function renderVotingActions() {
    const el = document.getElementById('vote-buttons');
    if (!el) return;
    if (hasVoted) {
        el.innerHTML = '<div class="voted-msg">✓ Vote cast</div>';
    } else {
        el.innerHTML = `
            <button class="vote-btn vote-for" onclick="castVote('for')">FOR</button>
            <button class="vote-btn vote-against" onclick="castVote('against')">AGAINST</button>
            <button class="vote-btn vote-abstain" onclick="castVote('abstain')">ABSTAIN</button>
            <button class="vote-btn vote-pass" onclick="castVote('pass')">PASS</button>
        `;
    }
}

function renderSpeakerList() {
    const el = document.getElementById('speaker-list');
    if (!el || !state) return;
    const speakers = state.status === 'mod_caucus' ? state.mod_caucus.speakers : state.gsl.speakers;
    const currentIdx = state.status === 'mod_caucus' ? state.mod_caucus.current_index : state.gsl.current_index;

    el.innerHTML = speakers.map((c, i) => `
        <div class="speaker-row ${i === currentIdx ? 'current' : ''} ${i < currentIdx ? 'done' : ''} ${c === country ? 'mine' : ''}">
            <span class="speaker-pos">${i + 1}</span>
            <span class="speaker-name">${c}${c === country ? ' (you)' : ''}</span>
            ${i === currentIdx ? '<span class="speaking-now">🎤</span>' : ''}
        </div>
    `).join('') || '<p class="empty">No speakers in list</p>';
}

function renderAnnouncements() {
    const el = document.getElementById('announcements-list');
    if (!el || !state) return;
    el.innerHTML = [...state.announcements].reverse().map(a => `
        <div class="announcement-item">
            <div class="announcement-time">${new Date(a.timestamp * 1000).toLocaleTimeString()}</div>
            <div class="announcement-text">${a.message}</div>
        </div>
    `).join('') || '<p class="empty">No announcements</p>';
}

function renderDocuments() {
    const el = document.getElementById('documents-list');
    if (!el || !state) return;
    const wps = state.working_papers || [];
    const drs = state.draft_resolutions || [];
    el.innerHTML = [
        ...wps.map(wp => `<div class="doc-item"><strong>WP:</strong> ${wp.title} <span class="doc-status">${wp.status}</span>
            ${!wp.signatories.includes(country) && !wp.sponsors.includes(country) ?
                `<button class="btn-sm" onclick="signDoc('working_papers','${wp.id}')">Sign</button>` : '<span class="doc-signed">(signed)</span>'}
        </div>`),
        ...drs.map(dr => `<div class="doc-item"><strong>DR:</strong> ${dr.title} <span class="doc-status">${dr.status}</span></div>`)
    ].join('') || '<p class="empty">No documents</p>';
}

function signDoc(docType, docId) {
    delegateEmit('sign_document', { doc_type: docType, doc_id: docId });
    showToast('Signed document', 'success');
}

// === TABS ===
function switchInfoTab(tab) {
    document.querySelectorAll('.info-tab-content').forEach(t => t.style.display = 'none');
    document.querySelectorAll('.info-tab-btn').forEach(b => b.classList.remove('active'));
    document.getElementById('info-' + tab).style.display = 'block';
    document.querySelector(`[data-info-tab="${tab}"]`).classList.add('active');
}

// Motion modal dynamic fields
document.addEventListener('DOMContentLoaded', () => {
    // Restore session
    const savedRoom = localStorage.getItem('delegateRoom');
    const savedCountry = localStorage.getItem('delegateCountry');
    if (savedRoom) document.getElementById('room-code-input').value = savedRoom;
    if (savedCountry) document.getElementById('country-input').value = savedCountry;

    switchInfoTab('speakers');

    document.getElementById('motion-type')?.addEventListener('change', updateMotionFields);

    // Allow Enter key to join
    document.getElementById('room-code-input')?.addEventListener('keydown', e => {
        if (e.key === 'Enter') document.getElementById('country-input').focus();
    });
    document.getElementById('country-input')?.addEventListener('keydown', e => {
        if (e.key === 'Enter') joinRoom();
    });
});

function updateMotionFields() {
    const type = document.getElementById('motion-type').value;
    const fields = document.getElementById('motion-dynamic-fields');
    if (type === 'mod_caucus') {
        fields.innerHTML = `
            <input type="text" id="motion-topic" placeholder="Topic" class="input-field">
            <div class="form-row">
                <label class="form-label-inline">Total time (s):
                    <input type="number" id="motion-total-time" value="300" class="input-field input-small">
                </label>
                <label class="form-label-inline">Speaker time (s):
                    <input type="number" id="motion-speaker-time" value="60" class="input-field input-small">
                </label>
            </div>
        `;
    } else if (type === 'unmod_caucus') {
        fields.innerHTML = `
            <div class="form-row">
                <label class="form-label-inline">Duration (s):
                    <input type="number" id="motion-duration" value="300" class="input-field input-small">
                </label>
            </div>
            <input type="text" id="motion-purpose" placeholder="Purpose" class="input-field">
        `;
    } else {
        fields.innerHTML = '';
    }
}
