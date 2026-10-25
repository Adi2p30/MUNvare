// Dependency-free smoke exercise of frontend/live_mun.js widget behavior.
import fs from 'fs';
import vm from 'vm';

const IDS = [
  'timerDuration', 'timerWarning', 'timerDisplay', 'startTimerBtn',
  'pauseTimerBtn', 'speechHistoryList', 'voteMotion', 'currentVotePanel',
  'currentVoteTitle', 'voteFavorInput', 'voteAgainstInput', 'voteAbstainInput',
  'voteFavorList', 'voteAgainstList', 'voteAbstainList', 'voteCountFavor',
  'voteCountAgainst', 'voteCountAbstain', 'voteHistoryList', 'allyInput',
  'potentialAllyInput', 'oppositionInput', 'strongAlliesList',
  'potentialAlliesList', 'oppositionList', 'interactionCountry',
  'interactionType', 'interactionNote', 'interactionLog', 'coalitionNotes',
  'actionItemInput', 'actionItemsList', 'keyPointInput', 'keyPointsList',
];

function makeSpan() {
  return {
    value: '',
    textContent: '',
    innerHTML: '',
    style: {},
    tagName: 'SPAN',
    querySelector() {
      return makeSpan();
    },
  };
}

function makeElement() {
  const span = makeSpan();
  return {
    value: '',
    textContent: '',
    innerHTML: '',
    style: {},
    querySelector() {
      return span;
    },
  };
}

const elements = Object.create(null);
for (const id of IDS) {
  elements[id] = makeElement();
}

function assert(condition, message) {
  if (!condition) {
    throw new Error(message);
  }
}

const notifications = [];
const fetchCalls = [];
let intervalCallback = null;

function AudioContextStub() {
  this.destination = {};
  this.currentTime = 0;
}
AudioContextStub.prototype.createOscillator = function createOscillator() {
  return {
    connect() {},
    frequency: { value: 0 },
    type: 'sine',
    start() {},
    stop() {},
  };
};
AudioContextStub.prototype.createGain = function createGain() {
  return {
    connect() {},
    gain: {
      setValueAtTime() {},
      exponentialRampToValueAtTime() {},
    },
  };
};

globalThis.window = globalThis;
globalThis.document = {
  getElementById(id) {
    if (!Object.prototype.hasOwnProperty.call(elements, id)) {
      throw new Error('missing element id: ' + id);
    }
    return elements[id];
  },
};
globalThis.AudioContext = AudioContextStub;
globalThis.webkitAudioContext = AudioContextStub;
globalThis.showNotification = function showNotification(message, type) {
  notifications.push({ message, type });
};
globalThis.fetch = async function fetch(url, options = {}) {
  fetchCalls.push({
    url: String(url),
    method: String(options.method || 'GET').toUpperCase(),
    body: options.body == null ? '' : String(options.body),
  });
  return {
    ok: true,
    json: async () => ({ id: 'n1' }),
  };
};
globalThis.setInterval = function setInterval(callback) {
  intervalCallback = callback;
  return 1;
};
globalThis.clearInterval = function clearInterval() {};
globalThis.API_BASE = '/api';

const source = fs.readFileSync('/workspace/frontend/live_mun.js', 'utf8');
vm.runInThisContext(source, { filename: 'live_mun.js' });

function el(id) {
  return document.getElementById(id);
}

setQuickTimer(1.5);
assert(el('timerDuration').value === 1.5, 'timerDuration.value should be 1.5');
assert(el('timerDisplay').textContent === '00:00', 'timer display should start at 00:00');

startTimer();
assert(intervalCallback, 'setInterval callback was not stored');
assert(el('startTimerBtn').style.display === 'none', 'start button should hide while running');
intervalCallback();
intervalCallback();
assert(el('timerDisplay').textContent === '00:02', 'timer display should be 00:02 after two ticks');
pauseTimer();
assert(el('startTimerBtn').style.display === 'inline-block', 'pauseTimer should show the start button');
assert(el('pauseTimerBtn').style.display === 'none', 'pauseTimer should hide the pause button');

el('voteMotion').value = '';
const notesBeforeEmptyVote = notifications.length;
recordVote('draft');
assert(notifications.length === notesBeforeEmptyVote + 1, 'empty vote should notify');
assert(notifications.at(-1).type === 'error', 'empty vote notification should be an error');
assert(
  notifications.at(-1).message === 'Please enter motion/resolution title',
  'empty vote notification message mismatch: ' + notifications.at(-1).message,
);
assert(el('currentVotePanel').style.display !== 'block', 'empty vote must not open the panel');

el('voteMotion').value = 'Draft resolution';
recordVote('draft');
assert(el('currentVotePanel').style.display === 'block', 'recordVote should open the panel');
el('voteFavorInput').value = 'France';
addVote('favor');
el('voteAgainstInput').value = 'Germany';
addVote('against');
assert(Number(el('voteCountFavor').textContent) === 1, 'voteCountFavor should be 1');
assert(Number(el('voteCountAgainst').textContent) === 1, 'voteCountAgainst should be 1');
finalizeVote();
assert(el('currentVotePanel').style.display === 'none', 'finalizeVote should hide the panel');
const voteHtml = el('voteHistoryList').innerHTML;
assert(/PASSED|FAILED/.test(voteHtml), 'vote history missing PASSED or FAILED');
assert(voteHtml.includes('Draft resolution'), 'vote history missing Draft resolution');
// One favor and one against: favor is not greater, so the ballot is FAILED.
assert(voteHtml.includes('FAILED'), 'equal votes should be FAILED, got: ' + voteHtml);
assert(!voteHtml.includes('PASSED'), 'equal votes should not be PASSED');

el('allyInput').value = 'India';
addAlly('strong');
assert(el('strongAlliesList').innerHTML.includes('India'), 'strong allies should list India');
el('oppositionInput').value = 'China';
addAlly('opposition');
moveAlly('China', 'opposition', 'potential');
assert(el('potentialAlliesList').innerHTML.includes('China'), 'potential allies should list China');
assert(!el('oppositionList').innerHTML.includes('China'), 'opposition should no longer list China');
removeAlly('India', 'strong');
assert(!el('strongAlliesList').innerHTML.includes('India'), 'removeAlly should drop India');

const logBefore = el('interactionLog').innerHTML;
el('interactionCountry').value = '';
el('interactionType').value = '';
el('interactionNote').value = '';
logInteraction();
assert(el('interactionLog').innerHTML === logBefore, 'empty logInteraction should be a no-op');
el('interactionCountry').value = 'France';
el('interactionType').value = 'positive';
el('interactionNote').value = 'Co-sponsor';
logInteraction();
assert(el('interactionLog').innerHTML.includes('Co-sponsor'), 'interaction log should contain Co-sponsor');

el('actionItemInput').value = 'Send the chit';
addActionItem();
assert(el('actionItemsList').innerHTML.includes('Send the chit'), 'action item should render');
const actionId = el('actionItemsList').innerHTML.match(/toggleActionItem\((\d+)\)/);
assert(actionId, 'rendered action item should expose toggleActionItem id');
toggleActionItem(Number(actionId[1]));
assert(
  el('actionItemsList').innerHTML.includes('line-through'),
  'toggleActionItem should mark the item completed',
);
removeActionItem(Number(actionId[1]));
assert(!el('actionItemsList').innerHTML.includes('Send the chit'), 'removeActionItem should clear the item');

el('keyPointInput').value = 'Binding timeline';
addKeyPoint();
assert(el('keyPointsList').innerHTML.includes('Binding timeline'), 'key point should render');
const pointId = el('keyPointsList').innerHTML.match(/removeKeyPoint\((\d+)\)/);
assert(pointId, 'rendered key point should expose removeKeyPoint id');
removeKeyPoint(Number(pointId[1]));
assert(!el('keyPointsList').innerHTML.includes('Binding timeline'), 'removeKeyPoint should clear the point');

el('coalitionNotes').value = '';
const fetchesBefore = fetchCalls.length;
const notesBeforeSave = notifications.length;
await saveCoalitionNotes();
assert(fetchCalls.length === fetchesBefore, 'empty coalition notes must not fetch');
assert(notifications.length === notesBeforeSave + 1, 'empty coalition notes should notify');
assert(notifications.at(-1).type === 'error', 'empty coalition notes notification should be an error');
assert(
  notifications.at(-1).message === 'No coalition notes to save',
  'empty coalition notes message mismatch: ' + notifications.at(-1).message,
);

el('coalitionNotes').value = 'Bloc with India';
await saveCoalitionNotes();
assert(fetchCalls.length === fetchesBefore + 1, 'saveCoalitionNotes should fetch once');
const saved = fetchCalls.at(-1);
assert(saved.method === 'POST', 'coalition save should POST, got ' + saved.method);
assert(saved.body.includes('India'), 'POST body should include India');
assert(saved.body.includes('Bloc with India'), 'POST body should include Bloc with India');

console.log('SMOKE_OK');
