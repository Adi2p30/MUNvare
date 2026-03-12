// MUNvare Chair Interface
const socket = io();
let roomCode = null;
let chairToken = null;
let state = null;

// === SETUP ===
function setupRoom() {
    const committeeName = document.getElementById('committee-name').value.trim();
    const agenda = document.getElementById('agenda').value.trim();
    if (!committeeName) { alert('Enter committee name'); return; }
    socket.emit('create_room', { committee_name: committeeName, agenda });
}

socket.on('room_created', (data) => {
    roomCode = data.room_code;
    chairToken = data.chair_token;
    localStorage.setItem('chairToken', chairToken);
    localStorage.setItem('roomCode', roomCode);
    localStorage.setItem('committeeName', data.committee_name || document.getElementById('committee-name').value.trim());
    localStorage.setItem('agenda', data.agenda || document.getElementById('agenda').value.trim());
    document.getElementById('setup-screen').style.display = 'none';
    document.getElementById('main-interface').style.display = 'flex';
    document.getElementById('room-code-display').textContent = roomCode;
    const cName = data.committee_name || document.getElementById('committee-name').value.trim();
    document.getElementById('committee-title').textContent = cName;
    if (data.agenda) {
        document.getElementById('agenda-bar-text').textContent = data.agenda;
    }
    addDelegateInputs();
});

socket.on('room_state_updated', (newState) => {
    state = newState;
    renderAll();
});

socket.on('room_state', (newState) => {
    state = newState;
    renderAll();
});

socket.on('error', (data) => {
    alert('Error: ' + data.message);
});

socket.on('connect_error', () => {
    console.warn('Socket connection failed — running in offline/demo mode');
});

// === CHAIR HELPERS ===
function chairEmit(event, data = {}) {
    socket.emit(event, { ...data, room_code: roomCode, chair_token: chairToken });
}

// === DELEGATES ===
function startRollCall() {
    const textarea = document.getElementById('delegate-list-input');
    const delegates = textarea.value.split('\n').map(s => s.trim()).filter(Boolean);
    if (!delegates.length) { alert('Enter at least one delegate country'); return; }
    chairEmit('start_roll_call', { delegates });
}

function markAttendance(country, present) {
    chairEmit('mark_attendance', { country, present });
}

function filterDelegates() {
    const q = document.getElementById('delegate-search').value.toLowerCase();
    document.querySelectorAll('.delegate-item').forEach(el => {
        const name = el.querySelector('.delegate-name')?.textContent.toLowerCase() || '';
        el.style.display = name.includes(q) ? '' : 'none';
    });
}

function renderDelegates() {
    if (!state) return;
    const list = document.getElementById('delegate-list');
    const presentCount = state.delegates.filter(d => d.present).length;
    const totalCount = state.delegates.length;
    document.getElementById('delegate-count').textContent = `${presentCount}/${totalCount}`;

    list.innerHTML = state.delegates.map(d => `
        <div class="delegate-item ${d.present ? 'present' : ''} ${d.connected ? 'connected' : ''}">
            <span class="delegate-flag">${d.connected ? '🟢' : '⚪'}</span>
            <span class="delegate-name">${d.country}</span>
            <button class="btn-sm ${d.present ? 'btn-success' : 'btn-outline'}"
                    onclick="markAttendance('${escapeAttr(d.country)}', ${!d.present})">
                ${d.present ? 'P' : 'A'}
            </button>
        </div>
    `).join('');
}

// === GSL ===
function openGSL() {
    const time = parseInt(document.getElementById('gsl-speaker-time')?.value) || 90;
    chairEmit('open_gsl', { speaker_time: time });
}

function closeGSL() { chairEmit('close_gsl'); }

function addToGSL() {
    const sel = document.getElementById('gsl-add-country');
    const country = sel ? sel.value.trim() : '';
    if (country) {
        chairEmit('add_to_gsl', { country });
        if (sel) sel.value = '';
    }
}

function removeFromGSL(country) { chairEmit('remove_from_gsl', { country }); }

function nextSpeaker() { chairEmit('next_speaker'); }

function startTimer(timer) { chairEmit('start_speaker_timer', { timer }); }

function pauseTimer(timer) {
    const remaining = getCurrentRemaining(timer);
    chairEmit('pause_speaker_timer', { timer, remaining });
}

function resetTimer(timer) {
    let duration = 90;
    if (timer.includes('mod_caucus.speaker')) {
        duration = state?.mod_caucus?.speaker_time || 60;
    } else if (timer.includes('gsl')) {
        duration = state?.gsl?.speaker_time || 90;
    }
    chairEmit('reset_speaker_timer', { timer, duration });
}

function getCurrentRemaining(timerPath) {
    if (!state) return 0;
    const parts = timerPath.split('.');
    let obj = state;
    for (const p of parts.slice(0, -1)) obj = obj?.[p] || {};
    return (obj?.[parts[parts.length - 1]] || {}).remaining || 0;
}

function renderGSL() {
    if (!state) return;
    const gsl = state.gsl;
    if (!gsl) return;
    const currentSpeaker = gsl.speakers?.[gsl.current_index] || null;
    const presentDelegates = state.delegates.filter(d => d.present);

    document.getElementById('gsl-panel').innerHTML = `
        <div class="panel-header">
            <h3>General Speakers List</h3>
            <span class="status-badge ${gsl.open ? 'open' : 'closed'}">${gsl.open ? 'OPEN' : 'CLOSED'}</span>
        </div>
        <div class="timer-display">
            <div class="timer-value${gsl.timer?.running ? ' running' : ''}" id="gsl-timer-display">${formatTime(gsl.timer?.remaining ?? gsl.speaker_time ?? 90)}</div>
            <div class="current-speaker">${currentSpeaker ? `Speaking: <strong>${currentSpeaker}</strong>` : 'No current speaker'}</div>
            <div class="timer-controls">
                <button class="btn btn-success" onclick="startTimer('gsl.timer')">&#9654; Start</button>
                <button class="btn btn-secondary" onclick="pauseTimer('gsl.timer')">&#9646;&#9646; Pause</button>
                <button class="btn btn-outline" onclick="resetTimer('gsl.timer')">&#8634; Reset</button>
                <button class="btn btn-accent" onclick="nextSpeaker()">Next &#9658;&#9658;</button>
            </div>
        </div>
        <div class="speaker-controls">
            <div class="gsl-settings">
                Speaker time:
                <input type="number" id="gsl-speaker-time" value="${gsl.speaker_time ?? 90}" style="width:64px"> sec
            </div>
            <div class="add-speaker">
                <select id="gsl-add-country" class="input-field">
                    <option value="">-- Select country --</option>
                    ${presentDelegates.map(d => `<option value="${escapeAttr(d.country)}">${d.country}</option>`).join('')}
                </select>
                <button class="btn btn-primary" onclick="addToGSL()">Add</button>
            </div>
        </div>
        <div class="speaker-list">
            <h4>Speakers Queue (${gsl.speakers?.length ?? 0})</h4>
            ${gsl.speakers?.length ? gsl.speakers.map((c, i) => `
                <div class="speaker-item ${i === gsl.current_index ? 'current' : ''} ${i < gsl.current_index ? 'done' : ''}">
                    <span class="pos">${i + 1}</span>
                    <span class="name">${c}</span>
                    <button class="btn-sm btn-danger" onclick="removeFromGSL('${escapeAttr(c)}')">&#10005;</button>
                </div>
            `).join('') : '<div class="empty-state">No speakers queued</div>'}
        </div>
        <div class="gsl-actions">
            <button class="btn btn-primary" onclick="openGSL()">Open GSL</button>
            <button class="btn btn-secondary" onclick="closeGSL()">Close GSL</button>
        </div>
    `;
}

// === MOD CAUCUS ===
function startModCaucus() {
    const topicEl = document.getElementById('mod-topic');
    const topic = topicEl ? topicEl.value.trim() : '';
    const totalTime = parseInt(document.getElementById('mod-total-time')?.value) || 300;
    const speakerTime = parseInt(document.getElementById('mod-speaker-time')?.value) || 60;
    if (!topic) { alert('Enter topic'); return; }
    chairEmit('start_mod_caucus', { topic, total_time: totalTime, speaker_time: speakerTime });
}

function endModCaucus() { chairEmit('end_mod_caucus'); }

function nextModSpeaker() { chairEmit('next_mod_caucus_speaker'); }

function renderModCaucus() {
    if (!state) return;
    const mc = state.mod_caucus;
    if (!mc) return;
    const currentSpeaker = mc.speakers?.[mc.current_index] || null;

    document.getElementById('mod-panel').innerHTML = `
        <div class="panel-header">
            <h3>Moderated Caucus</h3>
            <span class="status-badge ${mc.active ? 'active' : 'inactive'}">${mc.active ? 'ACTIVE' : 'INACTIVE'}</span>
        </div>
        ${mc.active ? `
        <div class="caucus-info">
            <strong>Topic:</strong> ${mc.topic}<br>
            <strong>Total Time:</strong> ${formatTime(mc.timer?.remaining ?? mc.total_time)} / ${formatTime(mc.total_time)}<br>
            <strong>Speaker Time:</strong> ${formatTime(mc.speaker_timer?.remaining ?? mc.speaker_time)} / ${formatTime(mc.speaker_time)}
        </div>
        <div class="timer-display">
            <div class="timer-value" id="mod-timer-display">${formatTime(mc.timer?.remaining ?? mc.total_time)}</div>
            <div class="current-speaker">${currentSpeaker ? `Speaking: <strong>${currentSpeaker}</strong>` : 'No current speaker'}</div>
            <div class="timer-controls">
                <span class="text-muted text-sm bold">Total:</span>
                <button class="btn btn-success" onclick="startTimer('mod_caucus.timer')">&#9654;</button>
                <button class="btn btn-secondary" onclick="pauseTimer('mod_caucus.timer')">&#9646;&#9646;</button>
                &nbsp;
                <span class="text-muted text-sm bold">Speaker:</span>
                <button class="btn btn-success" onclick="startTimer('mod_caucus.speaker_timer')">&#9654;</button>
                <button class="btn btn-secondary" onclick="pauseTimer('mod_caucus.speaker_timer')">&#9646;&#9646;</button>
                <button class="btn btn-outline" onclick="resetTimer('mod_caucus.speaker_timer')">&#8634;</button>
                <button class="btn btn-accent" onclick="nextModSpeaker()">Next &#9658;&#9658;</button>
            </div>
        </div>
        <div class="speaker-list">
            <h4>Speakers (${mc.speakers?.length ?? 0})</h4>
            ${mc.speakers?.length ? mc.speakers.map((c, i) => `
                <div class="speaker-item ${i === mc.current_index ? 'current' : ''}">
                    <span class="pos">${i + 1}</span>
                    <span class="name">${c}</span>
                </div>
            `).join('') : '<div class="empty-state">No speakers</div>'}
        </div>
        <div class="mt-12">
            <button class="btn btn-danger" onclick="endModCaucus()">End Mod Caucus</button>
        </div>
        ` : `
        <div class="caucus-setup">
            <input type="text" id="mod-topic" placeholder="Caucus topic" class="input-field">
            <div class="time-inputs">
                <label>Total time (s): <input type="number" id="mod-total-time" value="300" class="input-field" style="width:80px"></label>
                <label>Speaker time (s): <input type="number" id="mod-speaker-time" value="60" class="input-field" style="width:80px"></label>
            </div>
            <button class="btn btn-primary" onclick="startModCaucus()">Start Mod Caucus</button>
        </div>
        `}
    `;
}

// === UNMOD CAUCUS ===
function startUnmodCaucus() {
    const duration = parseInt(document.getElementById('unmod-duration')?.value) || 300;
    const purpose = document.getElementById('unmod-purpose')?.value.trim() || '';
    chairEmit('start_unmod_caucus', { duration, purpose });
}

function endUnmodCaucus() { chairEmit('end_unmod_caucus'); }

function renderUnmodCaucus() {
    if (!state) return;
    const uc = state.unmod_caucus;
    if (!uc) return;
    document.getElementById('unmod-panel').innerHTML = `
        <div class="panel-header">
            <h3>Unmoderated Caucus</h3>
            <span class="status-badge ${uc.active ? 'active' : 'inactive'}">${uc.active ? 'ACTIVE' : 'INACTIVE'}</span>
        </div>
        ${uc.active ? `
        <div class="caucus-info">
            <strong>Purpose:</strong> ${uc.purpose || '—'}<br>
            <strong>Time Remaining:</strong> ${formatTime(uc.timer?.remaining ?? uc.duration)}
        </div>
        <div class="timer-display">
            <div class="timer-value${uc.timer?.running ? ' running' : ''}">${formatTime(uc.timer?.remaining ?? uc.duration)}</div>
            <div class="timer-controls">
                <button class="btn btn-success" onclick="startTimer('unmod_caucus.timer')">&#9654; Start</button>
                <button class="btn btn-secondary" onclick="pauseTimer('unmod_caucus.timer')">&#9646;&#9646; Pause</button>
            </div>
        </div>
        <button class="btn btn-danger" onclick="endUnmodCaucus()">End Unmod Caucus</button>
        ` : `
        <div class="caucus-setup">
            <input type="text" id="unmod-purpose" placeholder="Purpose (optional)" class="input-field">
            <label class="time-inputs" style="gap:8px;align-items:center">Duration (s):
                <input type="number" id="unmod-duration" value="300" class="input-field" style="width:90px">
            </label>
            <button class="btn btn-primary" onclick="startUnmodCaucus()">Start Unmod Caucus</button>
        </div>
        `}
    `;
}

// === VOTING ===
function startVoting() {
    const motion = document.getElementById('voting-motion')?.value.trim();
    const type = document.getElementById('voting-type')?.value;
    if (!motion) { alert('Enter motion'); return; }
    chairEmit('start_voting', { motion, type });
}

function endVoting() { chairEmit('end_voting'); }

function renderVoting() {
    if (!state) return;
    const v = state.voting;
    if (!v) return;
    const votes = v.votes || {};
    const forCount = Object.values(votes).filter(x => x === 'for').length;
    const againstCount = Object.values(votes).filter(x => x === 'against').length;
    const abstainCount = Object.values(votes).filter(x => x === 'abstain').length;

    document.getElementById('voting-panel').innerHTML = `
        <div class="panel-header">
            <h3>Voting Procedure</h3>
            <span class="status-badge ${v.active ? 'active' : 'inactive'}">${v.active ? 'OPEN' : 'CLOSED'}</span>
        </div>
        ${v.active ? `
        <div class="voting-info">
            <strong>Motion:</strong> ${v.motion}<br>
            <strong>Type:</strong> ${v.type}
        </div>
        <div class="vote-tally">
            ${Object.entries(votes).map(([c, vote]) => `<span class="vote-chip vote-${vote}">${c}: ${vote}</span>`).join('')}
            ${!Object.keys(votes).length ? '<p class="empty-state">Awaiting votes from delegates...</p>' : ''}
        </div>
        <div class="vote-summary">For: ${forCount} &nbsp;|&nbsp; Against: ${againstCount} &nbsp;|&nbsp; Abstain: ${abstainCount}</div>
        <button class="btn btn-primary" onclick="endVoting()">Close Voting</button>
        ` : `
        <div class="voting-setup">
            <input type="text" id="voting-motion" placeholder="Motion or resolution title" class="input-field">
            <select id="voting-type" class="input-field">
                <option value="procedural">Procedural</option>
                <option value="substantive">Substantive</option>
            </select>
            <button class="btn btn-primary" onclick="startVoting()">Open Voting</button>
        </div>
        ${v.result ? `
        <div class="vote-result">
            <h4>Last Vote Result</h4>
            <div class="vote-summary">For: ${v.result.for} &nbsp;|&nbsp; Against: ${v.result.against} &nbsp;|&nbsp; Abstain: ${v.result.abstain}</div>
            <div style="margin-top:8px; font-size:13px; color:${v.result.passed ? 'var(--success)' : 'var(--danger)'}; font-weight:600;">
                ${v.result.passed ? 'PASSED' : 'FAILED'}
            </div>
        </div>
        ` : ''}
        `}
    `;
}

// === DOCUMENTS ===
function renderDocuments() {
    if (!state) return;
    document.getElementById('docs-panel').innerHTML = `
        <div class="panel-header"><h3>Working Papers &amp; Draft Resolutions</h3></div>
        <div class="docs-section">
            <h4>Working Papers (${state.working_papers?.length ?? 0})</h4>
            ${state.working_papers?.length ? state.working_papers.map(wp => `
                <div class="doc-item status-${wp.status}">
                    <strong>${wp.title}</strong>
                    <span>Sponsors: ${wp.sponsors?.join(', ') || '—'}</span>
                    <span>Signatories: ${wp.signatories?.length ?? 0}</span>
                    <span>Status: <em>${wp.status}</em></span>
                    ${wp.status === 'submitted' ? `<button class="btn-sm btn-primary" onclick="acceptWP('${escapeAttr(wp.id)}')">Accept &rarr; Draft Res</button>` : ''}
                </div>
            `).join('') : '<p class="empty-state">No working papers submitted</p>'}
        </div>
        <div class="docs-section">
            <h4>Draft Resolutions (${state.draft_resolutions?.length ?? 0})</h4>
            ${state.draft_resolutions?.length ? state.draft_resolutions.map(dr => `
                <div class="doc-item status-${dr.status}">
                    <strong>${dr.title}</strong>
                    <span>Sponsors: ${dr.sponsors?.join(', ') || '—'}</span>
                    <span>Status: <em>${dr.status}</em></span>
                </div>
            `).join('') : '<p class="empty-state">No draft resolutions</p>'}
        </div>
    `;
}

function acceptWP(wpId) { chairEmit('accept_working_paper', { wp_id: wpId }); }

// === RIGHT PANEL ===
function renderMotions() {
    if (!state) return;
    const pending = (state.motions_queue || []).filter(m => m.status === 'proposed');
    const badge = document.getElementById('motions-badge');
    if (badge) badge.textContent = pending.length || '';
    if (badge) badge.style.display = pending.length ? '' : 'none';

    document.getElementById('motions-list').innerHTML = pending.length ? pending.map(m => `
        <div class="motion-item">
            <strong>${m.type}</strong> by ${m.proposer}
            <small>${m.details ? JSON.stringify(m.details) : ''}</small>
            <div class="motion-actions">
                <button class="btn-sm btn-success" onclick="decideMotion('${escapeAttr(m.id)}', true)">Accept</button>
                <button class="btn-sm btn-danger" onclick="decideMotion('${escapeAttr(m.id)}', false)">Reject</button>
            </div>
        </div>
    `).join('') : '<p class="empty-state">No pending motions</p>';
}

function decideMotion(motionId, accepted) {
    chairEmit(accepted ? 'accept_motion' : 'reject_motion', { motion_id: motionId });
}

function renderPoints() {
    if (!state) return;
    const pending = (state.points_queue || []).filter(p => p.status === 'pending');
    const badge = document.getElementById('points-badge');
    if (badge) badge.textContent = pending.length || '';
    if (badge) badge.style.display = pending.length ? '' : 'none';

    document.getElementById('points-list').innerHTML = pending.length ? pending.map(p => `
        <div class="point-item">
            <strong>${p.type}</strong> &mdash; ${p.country}
            <small>${p.details || ''}</small>
            <button class="btn-sm btn-primary" onclick="recognizePoint('${escapeAttr(p.id)}')">Recognize</button>
        </div>
    `).join('') : '<p class="empty-state">No pending points</p>';
}

function recognizePoint(pointId) { chairEmit('recognize_point', { point_id: pointId }); }

function renderRightOfReply() {
    if (!state) return;
    const pending = (state.right_of_reply_queue || []).filter(r => r.status === 'pending');
    const badge = document.getElementById('ror-badge');
    if (badge) badge.textContent = pending.length || '';
    if (badge) badge.style.display = pending.length ? '' : 'none';

    document.getElementById('ror-list').innerHTML = pending.length ? pending.map(r => `
        <div class="ror-item">
            <span><strong>${r.country}</strong> re: ${r.regarding}</span>
            <div class="ror-actions">
                <button class="btn-sm btn-success" onclick="grantROR('${escapeAttr(r.id)}')">Grant</button>
                <button class="btn-sm btn-danger" onclick="denyROR('${escapeAttr(r.id)}')">Deny</button>
            </div>
        </div>
    `).join('') : '';
}

function grantROR(reqId) { chairEmit('grant_right_of_reply', { req_id: reqId }); }
function denyROR(reqId) { chairEmit('deny_right_of_reply', { req_id: reqId }); }

// === SESSION CONTROLS ===
function startRollCallBtn() {
    addDelegateInputs();
    // Scroll the left panel into view if possible
    document.getElementById('delegate-setup').scrollIntoView({ behavior: 'smooth' });
}

function suspendSession() {
    if (confirm('Suspend session?')) chairEmit('suspend_session');
}

function resumeSession() { chairEmit('resume_session'); }

function adjournSession() {
    if (confirm('Adjourn session? This ends the committee.')) chairEmit('adjourn_session');
}

function sendAnnouncement() {
    const msg = document.getElementById('announcement-input').value.trim();
    if (!msg) return;
    chairEmit('send_announcement', { message: msg });
    document.getElementById('announcement-input').value = '';
}

// === TABS ===
function switchTab(tabName) {
    document.querySelectorAll('.tab-content').forEach(t => {
        t.style.display = 'none';
        t.classList.remove('active');
    });
    document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
    const panel = document.getElementById(tabName + '-panel');
    if (panel) {
        panel.style.display = 'block';
        panel.classList.add('active');
    }
    const btn = document.querySelector(`[data-tab="${tabName}"]`);
    if (btn) btn.classList.add('active');
}

// === TIMER DISPLAY ===
let timerDisplayInterval = null;

function startLocalTimerDisplay() {
    if (timerDisplayInterval) clearInterval(timerDisplayInterval);
    timerDisplayInterval = setInterval(() => {
        if (!state) return;

        // GSL timer
        const gslTimer = document.getElementById('gsl-timer-display');
        if (gslTimer && state.gsl?.timer?.running) {
            const elapsed = (Date.now() / 1000) - (state.gsl.timer.started_at || Date.now() / 1000);
            const remaining = Math.max(0, (state.gsl.timer.remaining || 0) - elapsed);
            gslTimer.textContent = formatTime(Math.floor(remaining));
            gslTimer.classList.toggle('low', remaining < 10);
        }

        // Mod caucus total timer
        const modTimer = document.getElementById('mod-timer-display');
        if (modTimer && state.mod_caucus?.timer?.running) {
            const elapsed = (Date.now() / 1000) - (state.mod_caucus.timer.started_at || Date.now() / 1000);
            const remaining = Math.max(0, (state.mod_caucus.timer.remaining || 0) - elapsed);
            modTimer.textContent = formatTime(Math.floor(remaining));
            modTimer.classList.toggle('low', remaining < 10);
        }
    }, 200);
}

function formatTime(seconds) {
    if (isNaN(seconds) || seconds < 0) seconds = 0;
    const m = Math.floor(seconds / 60);
    const s = Math.floor(seconds % 60);
    return `${m}:${s.toString().padStart(2, '0')}`;
}

// === ROOM CODE COPY ===
function copyRoomCode() {
    if (!roomCode) return;
    navigator.clipboard.writeText(roomCode).catch(() => {});
    const el = document.getElementById('room-code-display');
    const prev = el.textContent;
    el.textContent = 'Copied!';
    setTimeout(() => el.textContent = prev, 1500);
}

// === ADD DELEGATES UI ===
function addDelegateInputs() {
    document.getElementById('delegate-setup').style.display = 'block';
}

// === RENDER ALL ===
function renderAll() {
    if (!state) return;
    renderDelegates();
    renderGSL();
    renderModCaucus();
    renderUnmodCaucus();
    renderVoting();
    renderDocuments();
    renderMotions();
    renderPoints();
    renderRightOfReply();

    // Update status badge
    const statusEl = document.getElementById('committee-status');
    if (statusEl && state.status) {
        statusEl.textContent = state.status.replace(/_/g, ' ').toUpperCase();
        statusEl.className = 'status-badge ' + state.status;
    }
}

// === ESCAPE ATTR ===
function escapeAttr(str) {
    if (!str) return '';
    return String(str).replace(/'/g, "\\'").replace(/"/g, '&quot;');
}

// === INIT ===
document.addEventListener('DOMContentLoaded', () => {
    // Check if we have a saved room
    const savedCode = localStorage.getItem('roomCode');
    const savedToken = localStorage.getItem('chairToken');
    const savedName = localStorage.getItem('committeeName');
    const savedAgenda = localStorage.getItem('agenda');

    if (savedCode && savedToken) {
        roomCode = savedCode;
        chairToken = savedToken;
        socket.emit('join_room', { room_code: savedCode, role: 'chair', chair_token: savedToken });
        document.getElementById('setup-screen').style.display = 'none';
        document.getElementById('main-interface').style.display = 'flex';
        document.getElementById('room-code-display').textContent = savedCode;
        if (savedName) document.getElementById('committee-title').textContent = savedName;
        if (savedAgenda) document.getElementById('agenda-bar-text').textContent = savedAgenda;
        addDelegateInputs();
    }

    switchTab('gsl');
    startLocalTimerDisplay();

    // Tab buttons
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.addEventListener('click', () => switchTab(btn.dataset.tab));
    });

    // Announcement keyboard shortcut
    document.getElementById('announcement-input')?.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && (e.ctrlKey || e.metaKey)) {
            sendAnnouncement();
        }
    });

    // Delegate search
    document.getElementById('delegate-search')?.addEventListener('input', filterDelegates);

    // Clear saved room button
    document.getElementById('clear-room-btn')?.addEventListener('click', () => {
        if (confirm('Clear saved room and go back to setup?')) {
            localStorage.removeItem('roomCode');
            localStorage.removeItem('chairToken');
            localStorage.removeItem('committeeName');
            localStorage.removeItem('agenda');
            location.reload();
        }
    });
});
