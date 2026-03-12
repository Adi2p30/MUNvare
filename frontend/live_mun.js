// Live MUN Features JavaScript

// ============= Speech Transcription =============

let recognition = null;
let transcriptionText = '';
let isTranscribing = false;

function startTranscription() {
    if (!('webkitSpeechRecognition' in window) && !('SpeechRecognition' in window)) {
        showNotification('Speech recognition not supported in this browser. Please use Chrome or Edge.', 'error');
        return;
    }

    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    recognition = new SpeechRecognition();
    recognition.continuous = true;
    recognition.interimResults = true;
    recognition.lang = 'en-US';

    const output = document.getElementById('transcriptionOutput');
    const status = document.getElementById('recordingStatus');
    const speaker = document.getElementById('transcribeSpeaker').value;

    recognition.onstart = () => {
        isTranscribing = true;
        document.getElementById('startTranscriptionBtn').style.display = 'none';
        document.getElementById('stopTranscriptionBtn').style.display = 'block';
        status.innerHTML = '<span style="color: var(--danger);">● Recording...</span>';

        if (speaker) {
            transcriptionText += `\n\n### ${speaker}\n`;
            output.innerHTML = `<div style="margin-bottom: 16px;"><strong>${speaker}</strong></div>`;
        } else {
            output.innerHTML = '';
        }
    };

    recognition.onresult = (event) => {
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
            transcriptionText += finalTranscript;
        }

        const displayText = transcriptionText + interimTranscript;
        output.innerHTML = displayText.replace(/\n/g, '<br>') +
            '<span style="color: var(--text-secondary);">' + interimTranscript + '</span>';
        output.scrollTop = output.scrollHeight;
    };

    recognition.onerror = (event) => {
        console.error('Speech recognition error:', event.error);
        showNotification('Transcription error: ' + event.error, 'error');
        stopTranscription();
    };

    recognition.onend = () => {
        if (isTranscribing) {
            recognition.start(); // Restart if still transcribing
        }
    };

    recognition.start();
}

function stopTranscription() {
    if (recognition) {
        isTranscribing = false;
        recognition.stop();
        document.getElementById('startTranscriptionBtn').style.display = 'block';
        document.getElementById('stopTranscriptionBtn').style.display = 'none';
        document.getElementById('recordingStatus').textContent = '';
        showNotification('Recording stopped', 'success');
    }
}

function clearTranscription() {
    transcriptionText = '';
    document.getElementById('transcriptionOutput').innerHTML =
        '<p style="color: var(--text-secondary); text-align: center; padding: 40px 0;">Click "Start Recording" to begin transcribing speeches</p>';
}

async function saveTranscriptionToNotes() {
    if (!transcriptionText.trim()) {
        showNotification('No transcription to save', 'error');
        return;
    }

    const speaker = document.getElementById('transcribeSpeaker').value || 'Speech';
    const title = `Transcription - ${speaker} - ${new Date().toLocaleString()}`;

    try {
        const response = await fetch(`${API_BASE}/notes`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                title: title,
                content: transcriptionText,
                folder: 'general'
            })
        });

        if (response.ok) {
            showNotification('Transcription saved to notes!', 'success');
        }
    } catch (error) {
        showNotification('Error saving transcription', 'error');
    }
}

async function analyzeTranscribedSpeech() {
    if (!transcriptionText.trim()) {
        showNotification('No transcription to analyze', 'error');
        return;
    }

    const analysisDiv = document.getElementById('transcriptionAnalysis');
    analysisDiv.innerHTML = '<div class="loading"></div> Analyzing speech...';
    analysisDiv.style.display = 'block';

    try {
        const response = await fetch(`${API_BASE}/chat`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                message: `Analyze this MUN speech and provide:\n1. Main arguments\n2. Strengths\n3. Weaknesses\n4. Suggested POI questions\n5. Counter-arguments\n\nSpeech:\n${transcriptionText}`
            })
        });

        const data = await response.json();
        analysisDiv.innerHTML = `<h4>Speech Analysis</h4>${renderMarkdown(data.response)}`;
    } catch (error) {
        analysisDiv.innerHTML = '<p style="color: var(--danger);">Error analyzing speech</p>';
    }
}

// ============= Live Notes =============

let actionItems = [];
let keyPoints = [];

function addActionItem() {
    const input = document.getElementById('actionItemInput');
    const item = input.value.trim();

    if (!item) return;

    actionItems.push({
        id: Date.now(),
        text: item,
        completed: false,
        timestamp: new Date().toLocaleTimeString()
    });

    input.value = '';
    renderActionItems();
}

function renderActionItems() {
    const list = document.getElementById('actionItemsList');
    list.innerHTML = actionItems.map(item => `
        <div style="padding: 8px; background: var(--bg-secondary); border-radius: 4px; margin-bottom: 8px; display: flex; align-items: center; gap: 8px;">
            <input type="checkbox" ${item.completed ? 'checked' : ''} onchange="toggleActionItem(${item.id})" />
            <span style="flex: 1; ${item.completed ? 'text-decoration: line-through; opacity: 0.6;' : ''}">${item.text}</span>
            <span style="font-size: 11px; color: var(--text-secondary);">${item.timestamp}</span>
            <button onclick="removeActionItem(${item.id})" style="background: none; border: none; color: var(--danger); cursor: pointer;">×</button>
        </div>
    `).join('');
}

function toggleActionItem(id) {
    const item = actionItems.find(i => i.id === id);
    if (item) {
        item.completed = !item.completed;
        renderActionItems();
    }
}

function removeActionItem(id) {
    actionItems = actionItems.filter(i => i.id !== id);
    renderActionItems();
}

function addKeyPoint() {
    const input = document.getElementById('keyPointInput');
    const point = input.value.trim();

    if (!point) return;

    keyPoints.push({
        id: Date.now(),
        text: point,
        timestamp: new Date().toLocaleTimeString()
    });

    input.value = '';
    renderKeyPoints();
}

function renderKeyPoints() {
    const list = document.getElementById('keyPointsList');
    list.innerHTML = keyPoints.map(point => `
        <div style="padding: 12px; background: var(--bg-secondary); border-radius: 8px; border-left: 3px solid var(--accent);">
            <div style="font-weight: 500; margin-bottom: 4px;">${point.text}</div>
            <div style="font-size: 11px; color: var(--text-secondary); display: flex; justify-content: space-between;">
                <span>${point.timestamp}</span>
                <button onclick="removeKeyPoint(${point.id})" style="background: none; border: none; color: var(--danger); cursor: pointer; padding: 0;">Remove</button>
            </div>
        </div>
    `).join('');
}

function removeKeyPoint(id) {
    keyPoints = keyPoints.filter(p => p.id !== id);
    renderKeyPoints();
}

async function saveLiveNotes() {
    const notes = document.getElementById('liveNotesInput').value;

    if (!notes.trim()) {
        showNotification('No notes to save', 'error');
        return;
    }

    let fullContent = `# Session Notes - ${new Date().toLocaleString()}\n\n## Notes\n${notes}\n\n`;

    if (actionItems.length > 0) {
        fullContent += `## Action Items\n`;
        actionItems.forEach(item => {
            fullContent += `- [${item.completed ? 'x' : ' '}] ${item.text}\n`;
        });
        fullContent += '\n';
    }

    if (keyPoints.length > 0) {
        fullContent += `## Key Points\n`;
        keyPoints.forEach(point => {
            fullContent += `- ${point.text}\n`;
        });
    }

    try {
        const response = await fetch(`${API_BASE}/notes`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                title: `Session Notes - ${new Date().toLocaleDateString()}`,
                content: fullContent,
                folder: 'general'
            })
        });

        if (response.ok) {
            showNotification('Session notes saved!', 'success');
        }
    } catch (error) {
        showNotification('Error saving notes', 'error');
    }
}

// ============= Speaker Timer =============

let timerInterval = null;
let timerSeconds = 0;
let timerDuration = 120; // Default 2 minutes
let timerWarningTime = 30;
let timerRunning = false;
let speechHistory = [];

function startTimer() {
    if (timerRunning) return;

    timerDuration = parseFloat(document.getElementById('timerDuration').value) * 60;
    timerWarningTime = parseInt(document.getElementById('timerWarning').value);
    timerSeconds = 0;
    timerRunning = true;

    document.getElementById('startTimerBtn').style.display = 'none';
    document.getElementById('pauseTimerBtn').style.display = 'inline-block';

    timerInterval = setInterval(() => {
        timerSeconds++;
        updateTimerDisplay();

        // Warning alert
        const remaining = timerDuration - timerSeconds;
        if (remaining === timerWarningTime) {
            playBeep();
            document.getElementById('timerDisplay').style.color = 'var(--warning)';
        }

        // Time up
        if (timerSeconds >= timerDuration) {
            playBeep();
            playBeep();
            pauseTimer();
            document.getElementById('timerDisplay').style.color = 'var(--danger)';

            // Add to history
            speechHistory.push({
                duration: formatTime(timerSeconds),
                timestamp: new Date().toLocaleTimeString(),
                exceeded: true
            });
            renderSpeechHistory();
        }
    }, 1000);
}

function pauseTimer() {
    if (!timerRunning) return;

    timerRunning = false;
    clearInterval(timerInterval);

    document.getElementById('startTimerBtn').style.display = 'inline-block';
    document.getElementById('pauseTimerBtn').style.display = 'none';

    // Add to history if timer was running
    if (timerSeconds > 5) {
        speechHistory.push({
            duration: formatTime(timerSeconds),
            timestamp: new Date().toLocaleTimeString(),
            exceeded: timerSeconds > timerDuration
        });
        renderSpeechHistory();
    }
}

function resetTimer() {
    pauseTimer();
    timerSeconds = 0;
    updateTimerDisplay();
    document.getElementById('timerDisplay').style.color = 'var(--accent)';
}

function setQuickTimer(minutes) {
    document.getElementById('timerDuration').value = minutes;
    resetTimer();
}

function updateTimerDisplay() {
    document.getElementById('timerDisplay').textContent = formatTime(timerSeconds);
}

function formatTime(seconds) {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
}

function playBeep() {
    const audioContext = new (window.AudioContext || window.webkitAudioContext)();
    const oscillator = audioContext.createOscillator();
    const gainNode = audioContext.createGain();

    oscillator.connect(gainNode);
    gainNode.connect(audioContext.destination);

    oscillator.frequency.value = 800;
    oscillator.type = 'sine';

    gainNode.gain.setValueAtTime(0.3, audioContext.currentTime);
    gainNode.gain.exponentialRampToValueAtTime(0.01, audioContext.currentTime + 0.5);

    oscillator.start(audioContext.currentTime);
    oscillator.stop(audioContext.currentTime + 0.5);
}

function renderSpeechHistory() {
    const list = document.getElementById('speechHistoryList');
    list.innerHTML = speechHistory.slice().reverse().map((speech, i) => `
        <div style="padding: 8px; background: var(--bg-tertiary); border-radius: 4px; margin-bottom: 4px; display: flex; justify-content: space-between;">
            <span>${speech.duration}</span>
            <span style="font-size: 12px; color: var(--text-secondary);">${speech.timestamp}</span>
            ${speech.exceeded ? '<span style="color: var(--danger); font-size: 12px;">Exceeded</span>' : ''}
        </div>
    `).join('') || '<p style="color: var(--text-secondary); text-align: center; padding: 20px 0;">No speeches recorded yet</p>';
}

// ============= Vote Tracker =============

let currentVote = null;
let voteHistory = [];

function recordVote(type) {
    const motion = document.getElementById('voteMotion').value.trim();

    if (!motion) {
        showNotification('Please enter motion/resolution title', 'error');
        return;
    }

    currentVote = {
        id: Date.now(),
        motion: motion,
        type: type,
        favor: [],
        against: [],
        abstain: [],
        timestamp: new Date().toLocaleString()
    };

    document.getElementById('currentVotePanel').style.display = 'block';
    document.getElementById('currentVoteTitle').querySelector('span').textContent = motion;
    clearVoteLists();
    updateVoteCounts();
}

function addVote(voteType) {
    if (!currentVote) return;

    const inputId = `vote${voteType.charAt(0).toUpperCase() + voteType.slice(1)}Input`;
    const country = document.getElementById(inputId).value.trim();

    if (!country) return;

    currentVote[voteType].push(country);
    document.getElementById(inputId).value = '';
    renderVoteList(voteType);
    updateVoteCounts();
}

function renderVoteList(voteType) {
    const list = document.getElementById(`vote${voteType.charAt(0).toUpperCase() + voteType.slice(1)}List`);
    list.innerHTML = currentVote[voteType].map((country, index) => `
        <div style="padding: 4px 8px; background: var(--bg-tertiary); border-radius: 4px; margin-bottom: 4px; display: flex; justify-content: space-between; align-items: center;">
            <span style="font-size: 13px;">${country}</span>
            <button onclick="removeVote('${voteType}', ${index})" style="background: none; border: none; color: var(--danger); cursor: pointer; padding: 0 4px;">×</button>
        </div>
    `).join('');
}

function removeVote(voteType, index) {
    currentVote[voteType].splice(index, 1);
    renderVoteList(voteType);
    updateVoteCounts();
}

function clearVoteLists() {
    ['favor', 'against', 'abstain'].forEach(type => {
        document.getElementById(`vote${type.charAt(0).toUpperCase() + type.slice(1)}List`).innerHTML = '';
    });
}

function updateVoteCounts() {
    document.getElementById('voteCountFavor').textContent = currentVote.favor.length;
    document.getElementById('voteCountAgainst').textContent = currentVote.against.length;
    document.getElementById('voteCountAbstain').textContent = currentVote.abstain.length;
}

function finalizeVote() {
    if (!currentVote) return;

    const totalVotes = currentVote.favor.length + currentVote.against.length;
    const passed = currentVote.favor.length > currentVote.against.length;

    voteHistory.push({
        ...currentVote,
        passed: passed,
        totalVotes: totalVotes
    });

    currentVote = null;
    document.getElementById('currentVotePanel').style.display = 'none';
    document.getElementById('voteMotion').value = '';
    renderVoteHistory();

    showNotification(`Vote recorded: ${passed ? 'PASSED' : 'FAILED'}`, passed ? 'success' : 'error');
}

function renderVoteHistory() {
    const list = document.getElementById('voteHistoryList');
    list.innerHTML = voteHistory.slice().reverse().map(vote => `
        <div style="padding: 16px; background: var(--bg-tertiary); border-radius: 8px; margin-bottom: 12px; border-left: 4px solid ${vote.passed ? 'var(--success)' : 'var(--danger)'};">
            <div style="display: flex; justify-content: space-between; margin-bottom: 8px;">
                <strong>${vote.motion}</strong>
                <span style="color: ${vote.passed ? 'var(--success)' : 'var(--danger)'}; font-weight: bold;">
                    ${vote.passed ? 'PASSED' : 'FAILED'}
                </span>
            </div>
            <div style="font-size: 13px; color: var(--text-secondary); margin-bottom: 8px;">
                ${vote.type} • ${vote.timestamp}
            </div>
            <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 8px; font-size: 13px;">
                <div><strong style="color: var(--success);">For:</strong> ${vote.favor.length}</div>
                <div><strong style="color: var(--danger);">Against:</strong> ${vote.against.length}</div>
                <div><strong style="color: var(--text-secondary);">Abstain:</strong> ${vote.abstain.length}</div>
            </div>
        </div>
    `).join('') || '<p style="color: var(--text-secondary); text-align: center; padding: 20px 0;">No votes recorded yet</p>';
}

// ============= Ally Tracker =============

let allies = {
    strong: [],
    potential: [],
    opposition: []
};

let interactions = [];

function addAlly(type) {
    const inputId = type === 'strong' ? 'allyInput' : type === 'potential' ? 'potentialAllyInput' : 'oppositionInput';
    const country = document.getElementById(inputId).value.trim();

    if (!country) return;

    // Remove from other lists if exists
    Object.keys(allies).forEach(key => {
        allies[key] = allies[key].filter(c => c !== country);
    });

    allies[type].push(country);
    document.getElementById(inputId).value = '';
    renderAllies();
}

function renderAllies() {
    renderAllyList('strong', 'strongAlliesList');
    renderAllyList('potential', 'potentialAlliesList');
    renderAllyList('opposition', 'oppositionList');
}

function renderAllyList(type, listId) {
    const list = document.getElementById(listId);
    list.innerHTML = allies[type].map(country => `
        <div style="padding: 8px; background: var(--bg-secondary); border-radius: 4px; margin-bottom: 8px; display: flex; justify-content: space-between; align-items: center;">
            <span>${country}</span>
            <div>
                ${type !== 'strong' ? `<button onclick="moveAlly('${country}', '${type}', 'strong')" style="background: none; border: none; color: var(--success); cursor: pointer; padding: 0 4px;" title="Move to strong allies">↑</button>` : ''}
                ${type !== 'potential' ? `<button onclick="moveAlly('${country}', '${type}', 'potential')" style="background: none; border: none; color: var(--warning); cursor: pointer; padding: 0 4px;" title="Move to potential">~</button>` : ''}
                ${type !== 'opposition' ? `<button onclick="moveAlly('${country}', '${type}', 'opposition')" style="background: none; border: none; color: var(--danger); cursor: pointer; padding: 0 4px;" title="Move to opposition">↓</button>` : ''}
                <button onclick="removeAlly('${country}', '${type}')" style="background: none; border: none; color: var(--text-secondary); cursor: pointer; padding: 0 4px;">×</button>
            </div>
        </div>
    `).join('') || '<p style="color: var(--text-secondary); font-size: 12px; padding: 8px 0;">No countries added</p>';
}

function moveAlly(country, fromType, toType) {
    allies[fromType] = allies[fromType].filter(c => c !== country);
    allies[toType].push(country);
    renderAllies();
}

function removeAlly(country, type) {
    allies[type] = allies[type].filter(c => c !== country);
    renderAllies();
}

function logInteraction() {
    const country = document.getElementById('interactionCountry').value.trim();
    const type = document.getElementById('interactionType').value;
    const note = document.getElementById('interactionNote').value.trim();

    if (!country || !note) return;

    interactions.push({
        country: country,
        type: type,
        note: note,
        timestamp: new Date().toLocaleString()
    });

    document.getElementById('interactionCountry').value = '';
    document.getElementById('interactionNote').value = '';
    renderInteractionLog();
}

function renderInteractionLog() {
    const log = document.getElementById('interactionLog');
    const colors = {
        positive: 'var(--success)',
        neutral: 'var(--text-secondary)',
        negative: 'var(--danger)'
    };

    log.innerHTML = interactions.slice().reverse().map(interaction => `
        <div style="padding: 12px; background: var(--bg-tertiary); border-radius: 8px; margin-bottom: 8px; border-left: 3px solid ${colors[interaction.type]};">
            <div style="display: flex; justify-content: space-between; margin-bottom: 4px;">
                <strong>${interaction.country}</strong>
                <span style="font-size: 12px; color: var(--text-secondary);">${interaction.timestamp}</span>
            </div>
            <div style="font-size: 13px;">${interaction.note}</div>
        </div>
    `).join('') || '<p style="color: var(--text-secondary); text-align: center; padding: 20px 0;">No interactions logged yet</p>';
}

async function saveCoalitionNotes() {
    const notes = document.getElementById('coalitionNotes').value;

    if (!notes.trim()) {
        showNotification('No coalition notes to save', 'error');
        return;
    }

    let content = `# Coalition Tracking - ${new Date().toLocaleString()}\n\n`;
    content += `## Strong Allies\n${allies.strong.map(c => `- ${c}`).join('\n') || 'None'}\n\n`;
    content += `## Potential Allies\n${allies.potential.map(c => `- ${c}`).join('\n') || 'None'}\n\n`;
    content += `## Opposition\n${allies.opposition.map(c => `- ${c}`).join('\n') || 'None'}\n\n`;
    content += `## Notes\n${notes}\n\n`;

    if (interactions.length > 0) {
        content += `## Recent Interactions\n`;
        interactions.slice(-5).forEach(i => {
            content += `- **${i.country}** (${i.type}): ${i.note}\n`;
        });
    }

    try {
        const response = await fetch(`${API_BASE}/notes`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                title: `Coalition Notes - ${new Date().toLocaleDateString()}`,
                content: content,
                folder: 'lobbying'
            })
        });

        if (response.ok) {
            showNotification('Coalition notes saved!', 'success');
        }
    } catch (error) {
        showNotification('Error saving coalition notes', 'error');
    }
}
