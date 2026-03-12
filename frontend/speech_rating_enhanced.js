// Enhanced Speech Rating System
// Handles new concise analyses, summary, rewrite, and save functionality

// Store current speech and analyses
let currentSpeechText = '';
let currentGrammarAnalysis = '';
let currentEthicsAnalysis = '';
let currentImpactAnalysis = '';
let currentSummaryAndRewrite = '';

// Override the analyzeSpeech function to handle new flow
async function analyzeSpeech(analysisType) {
    const speechText = document.getElementById('speechTextInput').value.trim();

    if (!speechText) {
        showNotification('Please enter a speech to analyze', 'error');
        return;
    }

    currentSpeechText = speechText;
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

        // If all three analyses are done, generate summary and rewrite
        if (analysisType === 'comprehensive' && currentGrammarAnalysis && currentEthicsAnalysis && currentImpactAnalysis) {
            await generateSummaryAndRewrite(speechText, country, topic);
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
        currentGrammarAnalysis = result.analysis;
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
        currentEthicsAnalysis = result.analysis;
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
        currentImpactAnalysis = result.analysis;
        document.getElementById('impactContent').innerHTML = marked.parse(result.analysis);
        document.getElementById('impactResults').style.display = 'block';
        if (!silent) showNotification('Impact analysis complete!', 'success');
    }
}

async function generateSummaryAndRewrite(speechText, country, topic) {
    showNotification('Generating comprehensive summary and improved speech...', 'info');

    const response = await fetch(`${API_BASE}/speech/summary-and-rewrite`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            speech_text: speechText,
            grammar_analysis: currentGrammarAnalysis,
            ethics_analysis: currentEthicsAnalysis,
            impact_analysis: currentImpactAnalysis,
            country: country,
            topic: topic
        })
    });

    const result = await response.json();

    if (result.summary_and_rewrite) {
        currentSummaryAndRewrite = result.summary_and_rewrite;
        displaySummaryAndRewrite(result.summary_and_rewrite);
    }
}

function displaySummaryAndRewrite(summaryAndRewrite) {
    const container = document.getElementById('comprehensiveResults');

    const content = `
        <div class="markdown-content">${marked.parse(summaryAndRewrite)}</div>

        <div style="display: flex; gap: 12px; margin-top: 24px; padding-top: 16px; border-top: 1px solid var(--border);">
            <button onclick="saveRewriteToMemory()" class="btn btn-primary" style="flex: 1;">
                <svg class="icon icon-sm" fill="none" stroke="currentColor" viewBox="0 0 24 24" style="display: inline-block; vertical-align: middle; margin-right: 4px;">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 7H5a2 2 0 00-2 2v9a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-3m-1 4l-3 3m0 0l-3-3m3 3V4"/>
                </svg>
                Save to Memory
            </button>
            <button onclick="saveRewriteToNotes()" class="btn btn-secondary" style="flex: 1;">
                <svg class="icon icon-sm" fill="none" stroke="currentColor" viewBox="0 0 24 24" style="display: inline-block; vertical-align: middle; margin-right: 4px;">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"/>
                </svg>
                Save to Notes
            </button>
            <button onclick="copyRewrittenSpeech()" class="btn btn-secondary" style="flex: 1;">
                <svg class="icon icon-sm" fill="none" stroke="currentColor" viewBox="0 0 24 24" style="display: inline-block; vertical-align: middle; margin-right: 4px;">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z"/>
                </svg>
                Copy Speech
            </button>
        </div>
    `;

    container.innerHTML = content;
    container.style.display = 'block';
}

// Save functions
async function saveRewriteToMemory() {
    if (!currentSummaryAndRewrite) {
        showNotification('No analysis to save', 'error');
        return;
    }

    try {
        // Extract the improved speech from the summary
        const improvedSpeechMatch = currentSummaryAndRewrite.match(/## IMPROVED SPEECH:?\s*([\s\S]*)/i);
        const improvedSpeech = improvedSpeechMatch ? improvedSpeechMatch[1].trim() : currentSummaryAndRewrite;

        // Save to AI context/memory
        const response = await fetch(`${API_BASE}/chat`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                message: `Remember this improved speech for future reference:\n\n${improvedSpeech}`
            })
        });

        if (response.ok) {
            showNotification('Saved to memory! AI will remember this speech.', 'success');
        } else {
            throw new Error('Failed to save');
        }
    } catch (error) {
        showNotification('Error saving to memory: ' + error.message, 'error');
    }
}

async function saveRewriteToNotes() {
    if (!currentSummaryAndRewrite) {
        showNotification('No analysis to save', 'error');
        return;
    }

    try {
        const topic = document.getElementById('rateSpeechTopic').value || 'Untitled';
        const country = document.getElementById('rateSpeechCountry').value;

        let title = `Improved Speech - ${topic}`;
        if (country) title += ` (${country})`;

        const content = `# ${title}\n\n## Original Speech\n\n${currentSpeechText}\n\n---\n\n${currentSummaryAndRewrite}`;

        const response = await fetch(`${API_BASE}/notes`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                title: title,
                content: content
            })
        });

        if (response.ok) {
            showNotification('Saved to notes!', 'success');
            // Reload notes if on notes section
            if (typeof loadNotes === 'function') {
                loadNotes();
            }
        } else {
            throw new Error('Failed to save');
        }
    } catch (error) {
        showNotification('Error saving to notes: ' + error.message, 'error');
    }
}

function copyRewrittenSpeech() {
    if (!currentSummaryAndRewrite) {
        showNotification('No speech to copy', 'error');
        return;
    }

    // Extract just the improved speech section
    const improvedSpeechMatch = currentSummaryAndRewrite.match(/## IMPROVED SPEECH:?\s*([\s\S]*)/i);
    const improvedSpeech = improvedSpeechMatch ? improvedSpeechMatch[1].trim() : currentSummaryAndRewrite;

    // Remove markdown formatting markers
    const cleanSpeech = improvedSpeech
        .replace(/\[PAUSE\]/g, '...')
        .replace(/\[RAISE VOICE\]/g, '')
        .replace(/\[SLOW DOWN\]/g, '')
        .replace(/\[EMPHASIZE\]/g, '')
        .replace(/\*\*/g, '');

    navigator.clipboard.writeText(cleanSpeech).then(() => {
        showNotification('Speech copied to clipboard!', 'success');
    }).catch(() => {
        showNotification('Failed to copy to clipboard', 'error');
    });
}

console.log('✅ Enhanced speech rating system loaded');
