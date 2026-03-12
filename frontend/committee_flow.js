// Committee Flow JavaScript

let currentFlow = null;
let blockTemplates = [];
let editingBlockId = null;

// Initialize on page load
document.addEventListener('DOMContentLoaded', function() {
    loadFlowTemplates();
    loadFlows();
});

// ============= Flow Management =============

async function loadFlowTemplates() {
    try {
        const response = await fetch(`${API_BASE}/committee-flow/templates`);
        blockTemplates = await response.json();
        console.log('Loaded block templates:', blockTemplates);
    } catch (error) {
        console.error('Error loading templates:', error);
    }
}

async function loadFlows() {
    try {
        const response = await fetch(`${API_BASE}/committee-flow`);
        const flows = await response.json();

        const selector = document.getElementById('flowSelector');

        // Clear existing options except first
        selector.innerHTML = '<option value="">-- Select or Create a Flow --</option>';

        flows.forEach(flow => {
            const option = document.createElement('option');
            option.value = flow.id;
            option.textContent = flow.name;
            selector.appendChild(option);
        });

    } catch (error) {
        console.error('Error loading flows:', error);
    }
}

function showCreateFlowModal() {
    document.getElementById('createFlowModal').style.display = 'flex';
    document.getElementById('newFlowName').value = '';
    document.getElementById('newFlowName').focus();
}

function closeCreateFlowModal() {
    document.getElementById('createFlowModal').style.display = 'none';
}

async function createFlow() {
    const name = document.getElementById('newFlowName').value.trim();

    if (!name) {
        alert('Please enter a flow name');
        return;
    }

    try {
        const response = await fetch(`${API_BASE}/committee-flow`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ name })
        });

        const flow = await response.json();

        closeCreateFlowModal();
        await loadFlows();

        // Select the new flow
        document.getElementById('flowSelector').value = flow.id;
        selectFlow();

        showNotification('Flow created successfully!', 'success');

    } catch (error) {
        console.error('Error creating flow:', error);
        alert('Error creating flow');
    }
}

async function selectFlow() {
    const selector = document.getElementById('flowSelector');
    const flowId = selector.value;

    if (!flowId) {
        // No flow selected
        currentFlow = null;
        document.getElementById('noFlowMessage').style.display = 'block';
        document.getElementById('blocksPalette').style.display = 'none';
        document.getElementById('flowTimeline').style.display = 'none';
        document.getElementById('deleteFlowBtn').style.display = 'none';
        return;
    }

    try {
        const response = await fetch(`${API_BASE}/committee-flow/${flowId}`);
        currentFlow = await response.json();

        // Show flow interface
        document.getElementById('noFlowMessage').style.display = 'none';
        document.getElementById('blocksPalette').style.display = 'block';
        document.getElementById('flowTimeline').style.display = 'block';
        document.getElementById('deleteFlowBtn').style.display = 'inline-block';

        renderBlockTemplates();
        renderFlowBlocks();

    } catch (error) {
        console.error('Error loading flow:', error);
        alert('Error loading flow');
    }
}

async function deleteCurrentFlow() {
    if (!currentFlow) return;

    if (!confirm(`Delete "${currentFlow.name}"? This cannot be undone.`)) {
        return;
    }

    try {
        await fetch(`${API_BASE}/committee-flow/${currentFlow.id}`, {
            method: 'DELETE'
        });

        currentFlow = null;
        await loadFlows();
        document.getElementById('flowSelector').value = '';
        selectFlow();

        showNotification('Flow deleted', 'success');

    } catch (error) {
        console.error('Error deleting flow:', error);
        alert('Error deleting flow');
    }
}

// ============= Block Templates Rendering =============

function renderBlockTemplates() {
    const container = document.getElementById('blockTemplates');
    container.innerHTML = '';

    blockTemplates.forEach(template => {
        const card = document.createElement('div');
        card.className = 'block-template-card';
        card.innerHTML = `
            <div class="block-template-icon">${template.icon}</div>
            <div class="block-template-name">${template.name}</div>
            <div class="block-template-desc">${template.description}</div>
        `;
        card.onclick = () => addBlockToFlow(template);
        container.appendChild(card);
    });
}

// ============= Block Management =============

async function addBlockToFlow(template) {
    if (!currentFlow) return;

    try {
        const response = await fetch(`${API_BASE}/committee-flow/${currentFlow.id}/blocks`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                type: template.id,
                data: { ...template.default_data }
            })
        });

        const block = await response.json();

        // Reload flow
        await selectFlow();

        showNotification(`${template.name} added to flow`, 'success');

    } catch (error) {
        console.error('Error adding block:', error);
        alert('Error adding block');
    }
}

function renderFlowBlocks() {
    const container = document.getElementById('flowBlocks');
    const emptyMessage = document.getElementById('emptyFlowMessage');

    if (!currentFlow || !currentFlow.blocks || currentFlow.blocks.length === 0) {
        container.innerHTML = '';
        emptyMessage.style.display = 'block';
        return;
    }

    emptyMessage.style.display = 'none';
    container.innerHTML = '';

    currentFlow.blocks.forEach((block, index) => {
        const template = blockTemplates.find(t => t.id === block.type);
        if (!template) return;

        const blockEl = document.createElement('div');
        blockEl.className = `flow-block flow-block-${block.status}`;
        blockEl.dataset.blockId = block.id;

        // Status badge
        let statusBadge = '';
        if (block.status === 'active') {
            statusBadge = '<span class="block-status-badge block-status-active">Active</span>';
        } else if (block.status === 'completed') {
            statusBadge = '<span class="block-status-badge block-status-completed">✓ Completed</span>';
        }

        // Block content based on type
        let blockContent = renderBlockContent(block, template);

        blockEl.innerHTML = `
            <div class="flow-block-header">
                <div class="flow-block-number">${index + 1}</div>
                <div class="flow-block-icon">${template.icon}</div>
                <div class="flow-block-title">
                    <div class="flow-block-name">${template.name}</div>
                    ${statusBadge}
                </div>
                <div class="flow-block-actions">
                    ${block.status === 'pending' ?
                        `<button onclick="startBlock('${block.id}')" class="btn btn-sm" title="Start">
                            <svg class="icon icon-sm" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z"/><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z"/></svg>
                        </button>` : ''}
                    ${block.status === 'active' ?
                        `<button onclick="completeBlock('${block.id}')" class="btn btn-sm btn-primary" title="Complete">
                            <svg class="icon icon-sm" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"/></svg>
                        </button>` : ''}
                    <button onclick="editBlock('${block.id}')" class="btn btn-sm" title="Edit">
                        <svg class="icon icon-sm" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z"/></svg>
                    </button>
                    <button onclick="deleteBlock('${block.id}')" class="btn btn-sm btn-danger" title="Delete">
                        <svg class="icon icon-sm" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"/></svg>
                    </button>
                </div>
            </div>
            <div class="flow-block-content">
                ${blockContent}
            </div>
        `;

        container.appendChild(blockEl);
    });
}

function renderBlockContent(block, template) {
    const data = block.data;
    let content = '';

    switch (block.type) {
        case 'gsl':
            content = `
                <div class="block-detail"><strong>Speaker Time:</strong> ${data.speaker_time || 90}s</div>
                <div class="block-detail"><strong>Speakers:</strong> ${data.speakers?.length || 0} added</div>
            `;
            break;

        case 'moderated_caucus':
            content = `
                <div class="block-detail"><strong>Topic:</strong> ${data.topic || 'Not set'}</div>
                <div class="block-detail"><strong>Total Time:</strong> ${data.total_time || 10} minutes</div>
                <div class="block-detail"><strong>Speaker Time:</strong> ${data.speaker_time || 60}s</div>
            `;
            break;

        case 'unmoderated_caucus':
            content = `
                <div class="block-detail"><strong>Duration:</strong> ${data.duration || 10} minutes</div>
                <div class="block-detail"><strong>Purpose:</strong> ${data.purpose || 'General discussion'}</div>
            `;
            break;

        case 'crisis':
            content = `
                <div class="block-detail"><strong>Title:</strong> ${data.title || 'Crisis Update'}</div>
                <div class="block-detail"><strong>Description:</strong> ${data.description || 'Not set'}</div>
            `;
            break;

        case 'resolution_discussion':
            content = `
                <div class="block-detail"><strong>Resolution:</strong> ${data.resolution_title || 'Draft Resolution'}</div>
                <div class="block-detail"><strong>Sponsors:</strong> ${data.sponsors?.join(', ') || 'None'}</div>
            `;
            break;

        case 'amendment':
            content = `
                <div class="block-detail"><strong>Type:</strong> ${data.type || 'Friendly'} Amendment</div>
                <div class="block-detail"><strong>Proposer:</strong> ${data.proposer || 'Not set'}</div>
            `;
            break;

        case 'voting':
            content = `
                <div class="block-detail"><strong>Motion:</strong> ${data.motion || 'Not set'}</div>
                <div class="block-detail"><strong>Type:</strong> ${data.type || 'Substantive'}</div>
            `;
            break;

        case 'consultation':
            content = `
                <div class="block-detail"><strong>Duration:</strong> ${data.duration || 15} minutes</div>
                <div class="block-detail"><strong>Purpose:</strong> ${data.purpose || 'Resolution refinement'}</div>
            `;
            break;

        case 'right_of_reply':
            content = `
                <div class="block-detail"><strong>Country:</strong> ${data.country || 'Not set'}</div>
                <div class="block-detail"><strong>Responding to:</strong> ${data.responding_to || 'Not set'}</div>
            `;
            break;

        case 'break':
            content = `
                <div class="block-detail"><strong>Duration:</strong> ${data.duration || 15} minutes</div>
                <div class="block-detail"><strong>Type:</strong> ${data.type || 'Break'}</div>
            `;
            break;

        default:
            content = '<div class="block-detail">No details available</div>';
    }

    // Add notes if any
    if (block.notes && block.notes.length > 0) {
        content += `<div class="block-notes-section">
            <strong>Notes:</strong>
            <ul class="block-notes-list">
                ${block.notes.map(n => `<li>${n.text}</li>`).join('')}
            </ul>
        </div>`;
    }

    return content;
}

// ============= Block Actions =============

async function startBlock(blockId) {
    if (!currentFlow) return;

    try {
        await fetch(`${API_BASE}/committee-flow/${currentFlow.id}/blocks/${blockId}/start`, {
            method: 'POST'
        });

        await selectFlow();
        showNotification('Block started', 'success');

    } catch (error) {
        console.error('Error starting block:', error);
        alert('Error starting block');
    }
}

async function completeBlock(blockId) {
    if (!currentFlow) return;

    try {
        await fetch(`${API_BASE}/committee-flow/${currentFlow.id}/blocks/${blockId}/complete`, {
            method: 'POST'
        });

        await selectFlow();
        showNotification('Block completed', 'success');

    } catch (error) {
        console.error('Error completing block:', error);
        alert('Error completing block');
    }
}

function editBlock(blockId) {
    if (!currentFlow) return;

    const block = currentFlow.blocks.find(b => b.id === blockId);
    if (!block) return;

    const template = blockTemplates.find(t => t.id === block.type);
    if (!template) return;

    editingBlockId = blockId;

    document.getElementById('editBlockTitle').textContent = template.name;

    // Generate form based on block type
    const form = generateBlockEditForm(block, template);
    document.getElementById('editBlockForm').innerHTML = form;

    document.getElementById('editBlockModal').style.display = 'flex';
}

function generateBlockEditForm(block, template) {
    const data = block.data;
    let form = '';

    switch (block.type) {
        case 'gsl':
            form = `
                <div class="form-group">
                    <label>Speaker Time (seconds)</label>
                    <input type="number" id="edit_speaker_time" value="${data.speaker_time || 90}" />
                </div>
            `;
            break;

        case 'moderated_caucus':
            form = `
                <div class="form-group">
                    <label>Topic</label>
                    <input type="text" id="edit_topic" value="${data.topic || ''}" placeholder="Specific topic for discussion" />
                </div>
                <div class="form-group">
                    <label>Total Time (minutes)</label>
                    <input type="number" id="edit_total_time" value="${data.total_time || 10}" />
                </div>
                <div class="form-group">
                    <label>Speaker Time (seconds)</label>
                    <input type="number" id="edit_speaker_time" value="${data.speaker_time || 60}" />
                </div>
            `;
            break;

        case 'unmoderated_caucus':
            form = `
                <div class="form-group">
                    <label>Duration (minutes)</label>
                    <input type="number" id="edit_duration" value="${data.duration || 10}" />
                </div>
                <div class="form-group">
                    <label>Purpose</label>
                    <input type="text" id="edit_purpose" value="${data.purpose || ''}" />
                </div>
            `;
            break;

        case 'crisis':
            form = `
                <div class="form-group">
                    <label>Crisis Title</label>
                    <input type="text" id="edit_title" value="${data.title || ''}" />
                </div>
                <div class="form-group">
                    <label>Description</label>
                    <textarea id="edit_description" rows="4">${data.description || ''}</textarea>
                </div>
            `;
            break;

        case 'resolution_discussion':
            form = `
                <div class="form-group">
                    <label>Resolution Title</label>
                    <input type="text" id="edit_resolution_title" value="${data.resolution_title || ''}" />
                </div>
                <div class="form-group">
                    <label>Sponsors (comma-separated)</label>
                    <input type="text" id="edit_sponsors" value="${data.sponsors?.join(', ') || ''}" />
                </div>
            `;
            break;

        case 'amendment':
            form = `
                <div class="form-group">
                    <label>Amendment Text</label>
                    <textarea id="edit_amendment_text" rows="3">${data.amendment_text || ''}</textarea>
                </div>
                <div class="form-group">
                    <label>Proposer</label>
                    <input type="text" id="edit_proposer" value="${data.proposer || ''}" />
                </div>
                <div class="form-group">
                    <label>Type</label>
                    <select id="edit_type">
                        <option value="friendly" ${data.type === 'friendly' ? 'selected' : ''}>Friendly</option>
                        <option value="unfriendly" ${data.type === 'unfriendly' ? 'selected' : ''}>Unfriendly</option>
                    </select>
                </div>
            `;
            break;

        case 'voting':
            form = `
                <div class="form-group">
                    <label>Motion/Resolution</label>
                    <input type="text" id="edit_motion" value="${data.motion || ''}" />
                </div>
                <div class="form-group">
                    <label>Type</label>
                    <select id="edit_type">
                        <option value="substantive" ${data.type === 'substantive' ? 'selected' : ''}>Substantive</option>
                        <option value="procedural" ${data.type === 'procedural' ? 'selected' : ''}>Procedural</option>
                    </select>
                </div>
            `;
            break;

        case 'consultation':
            form = `
                <div class="form-group">
                    <label>Duration (minutes)</label>
                    <input type="number" id="edit_duration" value="${data.duration || 15}" />
                </div>
                <div class="form-group">
                    <label>Purpose</label>
                    <input type="text" id="edit_purpose" value="${data.purpose || ''}" />
                </div>
            `;
            break;

        case 'right_of_reply':
            form = `
                <div class="form-group">
                    <label>Country</label>
                    <input type="text" id="edit_country" value="${data.country || ''}" />
                </div>
                <div class="form-group">
                    <label>Responding to</label>
                    <input type="text" id="edit_responding_to" value="${data.responding_to || ''}" />
                </div>
            `;
            break;

        case 'break':
            form = `
                <div class="form-group">
                    <label>Duration (minutes)</label>
                    <input type="number" id="edit_duration" value="${data.duration || 15}" />
                </div>
                <div class="form-group">
                    <label>Type</label>
                    <select id="edit_type">
                        <option value="break" ${data.type === 'break' ? 'selected' : ''}>Break</option>
                        <option value="lunch" ${data.type === 'lunch' ? 'selected' : ''}>Lunch</option>
                        <option value="recess" ${data.type === 'recess' ? 'selected' : ''}>Recess</option>
                    </select>
                </div>
            `;
            break;

        default:
            form = '<p>No editable fields for this block type</p>';
    }

    return form;
}

async function saveBlockEdit() {
    if (!currentFlow || !editingBlockId) return;

    const block = currentFlow.blocks.find(b => b.id === editingBlockId);
    if (!block) return;

    // Collect form data based on block type
    const updatedData = { ...block.data };

    // Generic fields
    const fields = ['topic', 'duration', 'purpose', 'title', 'description', 'resolution_title',
                   'sponsors', 'amendment_text', 'proposer', 'type', 'motion', 'country',
                   'responding_to', 'speaker_time', 'total_time'];

    fields.forEach(field => {
        const input = document.getElementById(`edit_${field}`);
        if (input) {
            if (field === 'sponsors') {
                updatedData[field] = input.value.split(',').map(s => s.trim()).filter(s => s);
            } else if (input.type === 'number') {
                updatedData[field] = parseInt(input.value) || 0;
            } else {
                updatedData[field] = input.value;
            }
        }
    });

    try {
        await fetch(`${API_BASE}/committee-flow/${currentFlow.id}/blocks/${editingBlockId}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ data: updatedData })
        });

        closeEditBlockModal();
        await selectFlow();
        showNotification('Block updated', 'success');

    } catch (error) {
        console.error('Error updating block:', error);
        alert('Error updating block');
    }
}

function closeEditBlockModal() {
    document.getElementById('editBlockModal').style.display = 'none';
    editingBlockId = null;
}

async function deleteBlock(blockId) {
    if (!currentFlow) return;

    if (!confirm('Delete this block from the flow?')) {
        return;
    }

    try {
        await fetch(`${API_BASE}/committee-flow/${currentFlow.id}/blocks/${blockId}`, {
            method: 'DELETE'
        });

        await selectFlow();
        showNotification('Block deleted', 'success');

    } catch (error) {
        console.error('Error deleting block:', error);
        alert('Error deleting block');
    }
}

// ============= Export & Save =============

async function saveFlowToNotes() {
    if (!currentFlow) return;

    let content = `# Committee Flow: ${currentFlow.name}\n\n`;
    content += `Created: ${new Date(currentFlow.created_at).toLocaleString()}\n\n`;
    content += `---\n\n`;

    currentFlow.blocks.forEach((block, index) => {
        const template = blockTemplates.find(t => t.id === block.type);
        if (!template) return;

        content += `## ${index + 1}. ${template.icon} ${template.name}\n`;
        content += `**Status:** ${block.status}\n\n`;

        // Add block-specific details
        Object.entries(block.data).forEach(([key, value]) => {
            if (value && value !== '') {
                const label = key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
                content += `- **${label}:** ${Array.isArray(value) ? value.join(', ') : value}\n`;
            }
        });

        if (block.notes && block.notes.length > 0) {
            content += `\n**Notes:**\n`;
            block.notes.forEach(note => {
                content += `- ${note.text}\n`;
            });
        }

        content += `\n---\n\n`;
    });

    try {
        await fetch(`${API_BASE}/notes/save-research`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                title: `Committee Flow: ${currentFlow.name}`,
                content: content,
                folder: 'general'
            })
        });

        showNotification('Flow saved to notes!', 'success');

        if (confirm('Flow saved! Would you like to view your notes?')) {
            navigateTo('notes');
        }

    } catch (error) {
        console.error('Error saving to notes:', error);
        alert('Error saving to notes');
    }
}

function exportFlow() {
    if (!currentFlow) return;

    const flowData = JSON.stringify(currentFlow, null, 2);
    const blob = new Blob([flowData], { type: 'application/json' });
    const url = URL.createObjectURL(blob);

    const a = document.createElement('a');
    a.href = url;
    a.download = `committee_flow_${currentFlow.name.replace(/\s+/g, '_')}.json`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);

    showNotification('Flow exported!', 'success');
}
