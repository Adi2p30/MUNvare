// New features for MUNvare - append to app.js or merge

// ============= Global State =============
let currentConfig = null;
let currentChatId = null;
let allTemplates = [];
let allFolders = [];

// ============= Initialization =============
document.addEventListener('DOMContentLoaded', function() {
    // Load configuration
    loadConfiguration();

    // Load chat history
    loadChatHistory();

    // Load folders and templates
    loadFolders();
    loadTemplates();
});

// ============= Setup / Configuration =============

async function loadConfiguration() {
    try {
        const response = await fetch(`${API_BASE}/config`);
        currentConfig = await response.json();

        // Populate setup form
        if (currentConfig.my_delegate) {
            document.getElementById('setupCountry').value = currentConfig.my_delegate.country || '';
            document.getElementById('setupCommittee').value = currentConfig.my_delegate.committee || '';
            document.getElementById('setupAgenda').value = currentConfig.my_delegate.agenda || '';
            document.getElementById('setupPortfolio').value = currentConfig.my_delegate.portfolio || '';
        }

        // Load other delegates
        loadOtherDelegates();

        // Load committee info
        if (currentConfig.committee_info) {
            document.getElementById('setupStudyGuide').value = currentConfig.committee_info.study_guide || '';
            document.getElementById('setupPositionPaper').value = currentConfig.committee_info.position_paper_due || '';
        }

    } catch (error) {
        console.error('Error loading configuration:', error);
    }
}

async function saveMyDelegate() {
    const country = document.getElementById('setupCountry').value;
    const committee = document.getElementById('setupCommittee').value;
    const agenda = document.getElementById('setupAgenda').value;
    const portfolio = document.getElementById('setupPortfolio').value;

    if (!country || !committee || !agenda) {
        showNotification('Please fill in country, committee, and agenda', 'error');
        return;
    }

    try {
        const response = await fetch(`${API_BASE}/config/delegate`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ country, committee, agenda, portfolio })
        });

        currentConfig = await response.json();
        showNotification('Your delegate info saved! AI will now use this context.', 'success');

    } catch (error) {
        showNotification('Error saving delegate info', 'error');
    }
}

async function addOtherDelegate() {
    const country = document.getElementById('otherDelegateCountry').value.trim();

    if (!country) {
        showNotification('Please enter a country name', 'error');
        return;
    }

    try {
        await fetch(`${API_BASE}/config/delegates`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ country, notes: '' })
        });

        document.getElementById('otherDelegateCountry').value = '';
        loadConfiguration();
        showNotification('Delegate added', 'success');

    } catch (error) {
        showNotification('Error adding delegate', 'error');
    }
}

async function removeOtherDelegate(delegateId) {
    try {
        await fetch(`${API_BASE}/config/delegates/${delegateId}`, {
            method: 'DELETE'
        });

        loadConfiguration();
        showNotification('Delegate removed', 'success');

    } catch (error) {
        showNotification('Error removing delegate', 'error');
    }
}

function loadOtherDelegates() {
    const container = document.getElementById('otherDelegatesList');
    container.innerHTML = '';

    if (!currentConfig.other_delegates || currentConfig.other_delegates.length === 0) {
        container.innerHTML = '<p style="color: var(--text-secondary); font-size: 13px;">No other delegates added yet</p>';
        return;
    }

    currentConfig.other_delegates.forEach(delegate => {
        const div = document.createElement('div');
        div.className = 'delegate-item';
        div.innerHTML = `
            <div>${delegate.country}</div>
            <button onclick="removeOtherDelegate('${delegate.id}')" class="btn btn-danger">Remove</button>
        `;
        container.appendChild(div);
    });
}

async function saveCommitteeInfo() {
    const study_guide = document.getElementById('setupStudyGuide').value;
    const position_paper_due = document.getElementById('setupPositionPaper').value;

    try {
        await fetch(`${API_BASE}/config/committee`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                committee: currentConfig.my_delegate.committee,
                agenda: currentConfig.my_delegate.agenda,
                study_guide,
                position_paper_due
            })
        });

        showNotification('Committee info saved', 'success');

    } catch (error) {
        showNotification('Error saving committee info', 'error');
    }
}

// ============= Chat History =============

async function loadChatHistory() {
    try {
        const response = await fetch(`${API_BASE}/chats`);
        const chats = await response.json();

        const container = document.getElementById('chatHistoryList');
        container.innerHTML = '';

        if (chats.length === 0) {
            container.innerHTML = '<p style="padding: 12px; color: var(--text-secondary); font-size: 13px;">No chats yet</p>';
            return;
        }

        chats.forEach(chat => {
            const div = document.createElement('div');
            div.className = 'chat-history-item';
            if (currentChatId === chat.id) {
                div.classList.add('active');
            }

            div.innerHTML = `
                <div class="chat-history-item-title">${chat.title}</div>
                <div class="chat-history-item-date">${new Date(chat.updated_at).toLocaleDateString()}</div>
            `;

            div.onclick = () => loadChat(chat.id);
            container.appendChild(div);
        });

    } catch (error) {
        console.error('Error loading chat history:', error);
    }
}

async function createNewChat() {
    try {
        const response = await fetch(`${API_BASE}/chats`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ title: 'New Chat' })
        });

        const chat = await response.json();
        currentChatId = chat.id;

        // Clear messages
        document.getElementById('chatMessages').innerHTML = '';

        // Reload history
        loadChatHistory();

        showNotification('New chat created', 'success');

    } catch (error) {
        showNotification('Error creating chat', 'error');
    }
}

async function loadChat(chatId) {
    try {
        const response = await fetch(`${API_BASE}/chats/${chatId}`);
        const chat = await response.json();

        currentChatId = chatId;

        // Display messages
        const messagesContainer = document.getElementById('chatMessages');
        messagesContainer.innerHTML = '';

        chat.messages.forEach(msg => {
            addChatMessage(msg.content, msg.role, false);
        });

        // Update history UI
        loadChatHistory();

    } catch (error) {
        showNotification('Error loading chat', 'error');
    }
}

// Update send message to use chat ID
async function sendMessage() {
    const input = document.getElementById('chatInput');
    const message = input.value.trim();

    if (!message) return;

    // Add user message to UI
    addChatMessage(message, 'user');
    input.value = '';

    try {
        const response = await fetch(`${API_BASE}/chat`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                message: message,
                chat_id: currentChatId
            })
        });

        const data = await response.json();

        // Update current chat ID if new
        if (data.chat_id) {
            currentChatId = data.chat_id;
        }

        // Add assistant message with markdown
        addChatMessage(data.response, 'assistant');

        // Reload chat history to update
        loadChatHistory();

    } catch (error) {
        addChatMessage('Error: Could not connect to server. Please make sure the backend is running.', 'assistant');
    }
}

function addChatMessage(message, role, parseMarkdown = true) {
    const messagesContainer = document.getElementById('chatMessages');
    const messageDiv = document.createElement('div');
    messageDiv.className = `chat-message ${role}`;

    if (parseMarkdown && role === 'assistant') {
        messageDiv.innerHTML = renderMarkdown(message);
    } else {
        messageDiv.textContent = message;
    }

    messagesContainer.appendChild(messageDiv);
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
}

function renderMarkdown(text) {
    // Enhanced markdown rendering
    return text
        // Code blocks
        .replace(/```(\w+)?\n([\s\S]+?)```/g, '<pre><code>$2</code></pre>')
        // Inline code
        .replace(/`([^`]+)`/g, '<code>$1</code>')
        // Headers
        .replace(/^### (.+)$/gm, '<h3>$1</h3>')
        .replace(/^## (.+)$/gm, '<h2>$1</h2>')
        .replace(/^# (.+)$/gm, '<h1>$1</h1>')
        // Bold
        .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
        // Italic
        .replace(/\*(.+?)\*/g, '<em>$1</em>')
        // Lists
        .replace(/^- (.+)$/gm, '<li>$1</li>')
        .replace(/^(\d+)\. (.+)$/gm, '<li>$2</li>')
        // Wrap lists
        .replace(/(<li>.*<\/li>\n?)+/g, '<ul>$&</ul>')
        // Line breaks
        .replace(/\n\n/g, '</p><p>')
        .replace(/^(?!<[hul])/gm, '<p>')
        .replace(/$/gm, '</p>');
}

// ============= Templates and Folders =============

let selectedFolderId = null;
let collapsedFolders = {};

async function loadFolders() {
    try {
        const response = await fetch(`${API_BASE}/notes-v2/folders`);
        allFolders = await response.json();

        const container = document.getElementById('foldersList');
        container.innerHTML = '';

        allFolders.forEach(folder => {
            const div = document.createElement('div');
            div.className = 'folder-item';
            div.dataset.folderId = folder.id;
            div.innerHTML = `
                <span class="folder-icon">${folder.icon}</span>
                <span class="folder-name">${folder.name}</span>
                <span class="folder-count" id="folder-count-${folder.id}">0</span>
            `;

            // Make folder clickable to filter notes
            div.onclick = () => toggleFolder(folder.id);

            // Make folder a drop zone
            div.addEventListener('dragover', (e) => {
                e.preventDefault();
                div.classList.add('drag-over');
            });

            div.addEventListener('dragleave', () => {
                div.classList.remove('drag-over');
            });

            div.addEventListener('drop', (e) => {
                e.preventDefault();
                div.classList.remove('drag-over');
                const noteId = e.dataTransfer.getData('noteId');
                if (noteId) {
                    moveNoteToFolder(noteId, folder.id);
                }
            });

            if (selectedFolderId === folder.id) {
                div.classList.add('active');
            }

            container.appendChild(div);
        });

        // Count notes in each folder
        updateFolderCounts();

    } catch (error) {
        console.error('Error loading folders:', error);
    }
}

async function updateFolderCounts() {
    try {
        const response = await fetch(`${API_BASE}/notes`);
        const notes = await response.json();

        // Reset counts
        allFolders.forEach(folder => {
            const countEl = document.getElementById(`folder-count-${folder.id}`);
            if (countEl) countEl.textContent = '0';
        });

        // Count notes per folder
        notes.forEach(note => {
            if (note.folder) {
                const countEl = document.getElementById(`folder-count-${note.folder}`);
                if (countEl) {
                    countEl.textContent = parseInt(countEl.textContent) + 1;
                }
            }
        });
    } catch (error) {
        console.error('Error updating folder counts:', error);
    }
}

function toggleFolder(folderId) {
    if (selectedFolderId === folderId) {
        selectedFolderId = null; // Deselect if clicking same folder
    } else {
        selectedFolderId = folderId;
    }

    // Update folder UI
    document.querySelectorAll('.folder-item').forEach(item => {
        if (item.dataset.folderId === folderId && selectedFolderId === folderId) {
            item.classList.add('active');
        } else {
            item.classList.remove('active');
        }
    });

    // Reload notes with filter
    loadNotes();
}

async function moveNoteToFolder(noteId, folderId) {
    try {
        const response = await fetch(`${API_BASE}/notes/${noteId}/move-to-folder`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ folder_id: folderId })
        });

        if (response.ok) {
            showNotification('Note moved to folder!', 'success');
            loadNotes();
            updateFolderCounts();
        } else {
            showNotification('Error moving note', 'error');
        }
    } catch (error) {
        showNotification('Error moving note', 'error');
    }
}

async function loadTemplates() {
    try {
        const response = await fetch(`${API_BASE}/notes-v2/templates`);
        allTemplates = await response.json();

    } catch (error) {
        console.error('Error loading templates:', error);
    }
}

function showTemplateModal() {
    const modal = document.getElementById('templateModal');
    const container = document.getElementById('templatesList');

    container.innerHTML = '';

    allTemplates.forEach(template => {
        const div = document.createElement('div');
        div.className = 'template-card';
        div.innerHTML = `
            <h4>${template.name}</h4>
            <p>${template.folder}</p>
        `;
        div.onclick = () => createNoteFromTemplate(template.id);
        container.appendChild(div);
    });

    modal.style.display = 'flex';
}

function closeTemplateModal() {
    document.getElementById('templateModal').style.display = 'none';
}

async function createNoteFromTemplate(templateId) {
    try {
        const response = await fetch(`${API_BASE}/notes-v2/from-template`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ template_id: templateId })
        });

        const note = await response.json();

        closeTemplateModal();
        showNotification('Note created from template!', 'success');

        // Switch to notes section and load the note
        navigateTo('notes');
        loadNotes();

    } catch (error) {
        showNotification('Error creating note from template', 'error');
    }
}

// ============= Utility =============

function showNotification(message, type = 'info') {
    // Simple console notification for now
    console.log(`[${type.toUpperCase()}] ${message}`);

    // Could add a toast notification UI here
    const colors = {
        info: '#2196F3',
        success: '#4CAF50',
        error: '#f44336',
        warning: '#ff9800'
    };

    // Create temporary notification
    const notification = document.createElement('div');
    notification.style.cssText = `
        position: fixed;
        bottom: 20px;
        right: 20px;
        padding: 16px 24px;
        background: ${colors[type] || colors.info};
        color: white;
        border-radius: 4px;
        z-index: 10000;
        animation: slideIn 0.3s ease-out;
    `;
    notification.textContent = message;
    document.body.appendChild(notification);

    setTimeout(() => {
        notification.style.animation = 'slideOut 0.3s ease-out';
        setTimeout(() => notification.remove(), 300);
    }, 3000);
}

// Add CSS for animations
const style = document.createElement('style');
style.textContent = `
    @keyframes slideIn {
        from { transform: translateX(400px); opacity: 0; }
        to { transform: translateX(0); opacity: 1; }
    }
    @keyframes slideOut {
        from { transform: translateX(0); opacity: 1; }
        to { transform: translateX(400px); opacity: 0; }
    }
`;
document.head.appendChild(style);

// ============= SPEECH RATING & ANALYSIS =============

async function analyzeSpeech(analysisType) {
    const speechText = document.getElementById('speechTextInput').value.trim();

    if (!speechText) {
        showNotification('Please enter a speech to analyze', 'error');
        return;
    }

    const country = document.getElementById('rateSpeechCountry').value;
    const topic = document.getElementById('rateSpeechTopic').value;
    const committee = document.getElementById('rateSpeechCommittee').value;

    // Show loading
    document.getElementById('analysisLoading').style.display = 'block';
    document.getElementById('speechAnalysisResults').style.display = 'none';

    // Hide all result sections initially
    document.getElementById('grammarResults').style.display = 'none';
    document.getElementById('ethicsResults').style.display = 'none';
    document.getElementById('impactResults').style.display = 'none';
    document.getElementById('comprehensiveResults').style.display = 'none';

    try {
        if (analysisType === 'comprehensive' || analysisType === 'grammar') {
            await analyzeGrammar(speechText, analysisType === 'comprehensive');
        }

        if (analysisType === 'comprehensive' || analysisType === 'ethics') {
            await analyzeEthics(speechText, country, analysisType === 'comprehensive');
        }

        if (analysisType === 'comprehensive' || analysisType === 'impact') {
            await analyzeImpact(speechText, topic, committee, analysisType === 'comprehensive');
        }

        if (analysisType === 'comprehensive') {
            await analyzeComprehensive(speechText, country, topic, committee);
        }

        // Show results container
        document.getElementById('speechAnalysisResults').style.display = 'block';
        showNotification('Analysis complete!', 'success');

    } catch (error) {
        showNotification('Error analyzing speech: ' + error.message, 'error');
    } finally {
        document.getElementById('analysisLoading').style.display = 'none';
    }
}

async function analyzeGrammar(speechText, silent = false) {
    const response = await fetch(`${API_BASE}/speech/rate-grammar`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ speech_text: speechText })
    });

    const result = await response.json();

    if (result.analysis) {
        document.getElementById('grammarContent').innerHTML = marked.parse(result.analysis);
        document.getElementById('grammarResults').style.display = 'block';
        if (!silent) showNotification('Grammar analysis complete!', 'success');
    }
}

async function analyzeEthics(speechText, country, silent = false) {
    const response = await fetch(`${API_BASE}/speech/rate-ethics`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ speech_text: speechText, country: country })
    });

    const result = await response.json();

    if (result.analysis) {
        document.getElementById('ethicsContent').innerHTML = marked.parse(result.analysis);
        document.getElementById('ethicsResults').style.display = 'block';
        if (!silent) showNotification('Ethics analysis complete!', 'success');
    }
}

async function analyzeImpact(speechText, topic, committee, silent = false) {
    const response = await fetch(`${API_BASE}/speech/rate-impact`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ speech_text: speechText, topic: topic, committee: committee })
    });

    const result = await response.json();

    if (result.analysis) {
        document.getElementById('impactContent').innerHTML = marked.parse(result.analysis);
        document.getElementById('impactResults').style.display = 'block';
        if (!silent) showNotification('Impact analysis complete!', 'success');
    }
}

async function analyzeComprehensive(speechText, country, topic, committee) {
    const response = await fetch(`${API_BASE}/speech/rate-comprehensive`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            speech_text: speechText,
            country: country,
            topic: topic,
            committee: committee
        })
    });

    const result = await response.json();

    if (result.analysis) {
        document.getElementById('comprehensiveContent').innerHTML = marked.parse(result.analysis);
        document.getElementById('comprehensiveResults').style.display = 'block';
    }
}

// ============= CHIT GENERATOR =============

let currentChitType = 'poi'; // Default type

function selectChitType(type) {
    currentChitType = type;

    // Update button styles
    ['poi', 'lobby', 'general', 'directive', 'respond'].forEach(t => {
        const btn = document.getElementById(`chitType${t.charAt(0).toUpperCase() + t.slice(1)}`);
        if (t === type) {
            btn.classList.remove('btn-secondary');
            btn.classList.add('btn-primary');
        } else {
            btn.classList.remove('btn-primary');
            btn.classList.add('btn-secondary');
        }
    });

    // Hide all specific fields
    document.getElementById('chitPOIFields').style.display = 'none';
    document.getElementById('chitLobbyFields').style.display = 'none';
    document.getElementById('chitGeneralFields').style.display = 'none';
    document.getElementById('chitDirectiveFields').style.display = 'none';
    document.getElementById('chitResponseFields').style.display = 'none';

    // Show relevant fields
    const fieldsMap = {
        'poi': 'chitPOIFields',
        'lobby': 'chitLobbyFields',
        'general': 'chitGeneralFields',
        'directive': 'chitDirectiveFields',
        'respond': 'chitResponseFields'
    };

    if (fieldsMap[type]) {
        document.getElementById(fieldsMap[type]).style.display = 'block';
    }
}

async function generateChit() {
    const myCountry = document.getElementById('chitMyCountry').value;
    const toCountry = document.getElementById('chitToCountry').value;

    if (!toCountry && currentChitType !== 'respond') {
        showNotification('Please enter the target country', 'error');
        return;
    }

    // Show loading
    document.getElementById('chitLoading').style.display = 'block';
    document.getElementById('chitOutput').style.display = 'none';

    try {
        let result;

        switch (currentChitType) {
            case 'poi':
                result = await generatePOIChit(toCountry, myCountry);
                break;
            case 'lobby':
                result = await generateLobbyChit(toCountry, myCountry);
                break;
            case 'general':
                result = await generateGeneralChit(toCountry, myCountry);
                break;
            case 'directive':
                result = await generateDirectiveChit(toCountry, myCountry);
                break;
            case 'respond':
                result = await generateResponseChit(myCountry);
                break;
        }

        if (result && result.chit) {
            document.getElementById('chitContent').innerHTML = marked.parse(result.chit);
            document.getElementById('chitOutput').style.display = 'block';
            showNotification('Chit generated successfully!', 'success');
        }

    } catch (error) {
        showNotification('Error generating chit: ' + error.message, 'error');
    } finally {
        document.getElementById('chitLoading').style.display = 'none';
    }
}

async function generatePOIChit(toCountry, myCountry) {
    const topic = document.getElementById('chitPOITopic').value;
    const question = document.getElementById('chitPOIQuestion').value;

    const response = await fetch(`${API_BASE}/chit/poi`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            to_country: toCountry,
            my_country: myCountry,
            topic: topic,
            question: question
        })
    });

    return await response.json();
}

async function generateLobbyChit(toCountry, myCountry) {
    const topic = document.getElementById('chitLobbyTopic').value;
    const purpose = document.getElementById('chitLobbyPurpose').value;

    const response = await fetch(`${API_BASE}/chit/lobby`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            to_country: toCountry,
            my_country: myCountry,
            topic: topic,
            purpose: purpose
        })
    });

    return await response.json();
}

async function generateGeneralChit(toCountry, myCountry) {
    const message = document.getElementById('chitGeneralMessage').value;
    const tone = document.getElementById('chitGeneralTone').value;

    if (!message) {
        showNotification('Please enter a message', 'error');
        throw new Error('Message required');
    }

    const response = await fetch(`${API_BASE}/chit/general`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            to_country: toCountry,
            my_country: myCountry,
            message: message,
            tone: tone
        })
    });

    return await response.json();
}

async function generateDirectiveChit(toCountry, myCountry) {
    const directive = document.getElementById('chitDirectiveText').value;
    const urgency = document.getElementById('chitDirectiveUrgency').value;

    if (!directive) {
        showNotification('Please enter a directive', 'error');
        throw new Error('Directive required');
    }

    const response = await fetch(`${API_BASE}/chit/directive`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            to_country: toCountry,
            my_country: myCountry,
            directive: directive,
            urgency: urgency
        })
    });

    return await response.json();
}

async function generateResponseChit(myCountry) {
    const originalChit = document.getElementById('chitOriginalText').value;
    const responseType = document.getElementById('chitResponseType').value;

    if (!originalChit) {
        showNotification('Please paste the original chit', 'error');
        throw new Error('Original chit required');
    }

    const response = await fetch(`${API_BASE}/chit/respond`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            original_chit: originalChit,
            my_country: myCountry,
            response_type: responseType
        })
    });

    return await response.json();
}

function copyChit() {
    const chitContent = document.getElementById('chitContent').innerText;

    navigator.clipboard.writeText(chitContent).then(() => {
        showNotification('Chit copied to clipboard!', 'success');
    }).catch(() => {
        showNotification('Failed to copy to clipboard', 'error');
    });
}

// Initialize chit type selection on page load
document.addEventListener('DOMContentLoaded', function() {
    // Set default chit type
    setTimeout(() => {
        if (typeof selectChitType === 'function') {
            selectChitType('poi');
        }
    }, 100);
});

console.log('✅ New features loaded: Setup, Chat History, Templates, Speech Rating, Chit Generator');
