"""File and HTTP smoke checks for the MUN UI contract.

Reads frontend HTML/JS from disk and GETs the same files through the Flask
test client. Does not start a server.
"""
import os
import re
import subprocess
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
os.chdir(ROOT)
sys.path.insert(0, os.path.join(ROOT, 'backend'))
import app as mun  # noqa: E402

client = mun.app.test_client()
FRONTEND = os.path.join(ROOT, 'frontend')

PAGE_SCRIPTS = {
    'index.html': [
        'app.js',
        'app_new_features.js',
        'live_mun.js',
        'live_auto_notes.js',
        'session.js',
        'session_extensions.js',
        'notes_extensions.js',
        'speech_rating_enhanced.js',
        'committee_flow.js',
    ],
    'chair.html': ['chair.js'],
    'delegate.html': ['delegate.js'],
}

CDN_URLS = {
    'index.html': 'https://cdn.jsdelivr.net/npm/marked/marked.min.js',
    'chair.html': 'https://cdn.socket.io/4.7.2/socket.io.min.js',
    'delegate.html': 'https://cdn.socket.io/4.7.2/socket.io.min.js',
}

IGNORE_CALLEES = {
    'if', 'for', 'while', 'switch', 'catch', 'function', 'return',
    'console', 'document', 'event', 'parseInt', 'parseFloat', 'String',
    'Math', 'JSON', 'Object', 'Array', 'window', 'alert', 'confirm',
    'setTimeout', 'setInterval', 'clearInterval', 'clearTimeout',
    'getElementById', 'querySelector', 'preventDefault', 'stopPropagation',
    'focus',
}

LIVE_MUN_IDS = [
    'timerDuration', 'timerWarning', 'timerDisplay', 'startTimerBtn',
    'pauseTimerBtn', 'speechHistoryList', 'voteMotion', 'currentVotePanel',
    'currentVoteTitle', 'voteFavorInput', 'voteAgainstInput', 'voteAbstainInput',
    'voteFavorList', 'voteAgainstList', 'voteAbstainList', 'voteCountFavor',
    'voteCountAgainst', 'voteCountAbstain', 'voteHistoryList', 'allyInput',
    'potentialAllyInput', 'oppositionInput', 'strongAlliesList',
    'potentialAlliesList', 'oppositionList', 'interactionCountry',
    'interactionType', 'interactionNote', 'interactionLog', 'coalitionNotes',
    'actionItemInput', 'actionItemsList', 'keyPointInput', 'keyPointsList',
]

ONCLICK_RE = re.compile(
    r'''onclick\s*=\s*(?:"([^"]*)"|'([^']*)')''',
    re.I,
)
CALL_RE = re.compile(
    r'(?:(?P<recv>[A-Za-z_$][\w$]*)\s*\.\s*)?(?P<name>[A-Za-z_$][\w$]*)\s*\('
)
FUNC_RE = re.compile(
    r'\b(?:async\s+)?function\s+([A-Za-z_$][\w$]*)\s*\('
)
SCRIPT_SRC_RE = re.compile(
    r'<script\b[^>]*\bsrc\s*=\s*["\']([^"\']+)["\']',
    re.I,
)
LINK_RE = re.compile(r'<link\b[^>]*>', re.I)
NAV_RE = re.compile(r'''navigateTo\(\s*['"]([^'"]+)['"]\s*\)''')


def _read(name):
    path = os.path.join(FRONTEND, name)
    with open(path, encoding='utf-8') as handle:
        return handle.read()


def _is_remote(url):
    return url.startswith('http://') or url.startswith('https://')


def _stylesheet_hrefs(html):
    hrefs = []
    for tag in LINK_RE.findall(html):
        if not re.search(r'''\brel\s*=\s*['"]stylesheet['"]''', tag, re.I):
            continue
        match = re.search(r'''\bhref\s*=\s*['"]([^'"]+)['"]''', tag, re.I)
        if match:
            hrefs.append(match.group(1))
    return hrefs


def _local_asset_urls(html):
    urls = []
    for src in SCRIPT_SRC_RE.findall(html):
        if not _is_remote(src):
            urls.append(src)
    for href in _stylesheet_hrefs(html):
        if not _is_remote(href):
            urls.append(href)
    return urls


def _served(path):
    response = client.get('/' + path.lstrip('/'))
    return response.status_code, response.get_data(as_text=True)


def _defined_functions(script_names):
    """Function declarations in page-script load order."""
    ordered = []
    for name in script_names:
        source = _read(name)
        for match in FUNC_RE.finditer(source):
            ordered.append((match.group(1), name))
    return ordered


def _onclick_callees(html):
    callees = []
    for match in ONCLICK_RE.finditer(html):
        code = match.group(1) if match.group(1) is not None else match.group(2)
        for call in CALL_RE.finditer(code):
            recv = call.group('recv')
            name = call.group('name')
            if recv in IGNORE_CALLEES or name in IGNORE_CALLEES:
                continue
            callees.append(name)
    return callees


def _controls(html):
    """Opening tags that carry onclick, plus text up to the matching close tag."""
    found = []
    for match in re.finditer(r'<([a-zA-Z][\w:-]*)\b([^>]*)>', html):
        tag = match.group(1)
        attrs = match.group(2)
        onclick_match = ONCLICK_RE.search(attrs)
        if not onclick_match:
            continue
        onclick = onclick_match.group(1)
        if onclick is None:
            onclick = onclick_match.group(2)
        rest = html[match.end():]
        close = re.search(rf'</{re.escape(tag)}\s*>', rest, re.I)
        inner = rest[:close.start()] if close else ''
        text = re.sub(r'<[^>]+>', ' ', inner)
        text = re.sub(r'\s+', ' ', text).strip()
        found.append((onclick, text))
    return found


def _assert_control(html, onclick_snippet, label, source):
    for onclick, text in _controls(html):
        if onclick_snippet in onclick and label in text:
            return
    raise AssertionError(
        f'{source}: missing control label {label!r} onclick {onclick_snippet!r}'
    )


def test_local_assets_and_cdn_markers_are_served():
    index_disk = _read('index.html')
    status, served_index = _served('index.html')
    assert status == 200
    assert served_index == index_disk
    root_status, served_root = _served('')
    assert root_status == 200
    assert served_root == index_disk

    for page in PAGE_SCRIPTS:
        disk = _read(page)
        status, served = _served(page)
        assert status == 200, page
        assert served == disk, page
        cdn = CDN_URLS[page]
        assert cdn in disk, f'{page} missing CDN url {cdn}'
        assert cdn in served, f'served {page} missing CDN url {cdn}'

        for asset in _local_asset_urls(disk):
            asset_status, asset_body = _served(asset)
            assert asset_status == 200, f'{page} asset {asset} HTTP {asset_status}'
            assert asset_body == _read(os.path.basename(asset)), asset

        remote_scripts = [src for src in SCRIPT_SRC_RE.findall(disk) if _is_remote(src)]
        remote_styles = [href for href in _stylesheet_hrefs(disk) if _is_remote(href)]
        assert all(_is_remote(url) for url in remote_scripts + remote_styles)


def test_page_scripts_load_in_order_and_define_onclick_callees():
    for page, scripts in PAGE_SCRIPTS.items():
        html = _read(page)
        local_scripts = [
            src for src in SCRIPT_SRC_RE.findall(html) if not _is_remote(src)
        ]
        assert local_scripts == scripts, (
            f'{page} script order {local_scripts} != {scripts}'
        )
        defined = _defined_functions(scripts)
        defined_names = {name for name, _script in defined}
        for callee in _onclick_callees(html):
            assert callee in defined_names, (
                f'missing function: {callee} (onclick on {page})'
            )


def test_data_section_values_have_section_ids():
    html = _read('index.html')
    section_ids = set(re.findall(
        r'<section\b[^>]*\bid\s*=\s*["\']([^"\']+)["\']',
        html,
        re.I,
    ))
    for name in re.findall(r'''data-section\s*=\s*["']([^"']+)["']''', html):
        assert name in section_ids, f'missing section id: {name}'


def test_navigate_to_literals_resolve():
    index_html = _read('index.html')
    section_ids = set(re.findall(
        r'<section\b[^>]*\bid\s*=\s*["\']([^"\']+)["\']',
        index_html,
        re.I,
    ))
    known_ids = set(re.findall(r'''\bid\s*=\s*["']([^"']+)["']''', index_html))
    sources = ['index.html', 'chair.html', 'delegate.html']
    sources.extend(sorted(
        name for name in os.listdir(FRONTEND) if name.endswith('.js')
    ))
    seen = set()
    for name in sources:
        text = _read(name)
        for target in NAV_RE.findall(text):
            if target in seen:
                continue
            seen.add(target)
            assert target in section_ids or target in known_ids, (
                f'missing navigateTo target: {target}'
            )
    assert seen, 'expected navigateTo literals'


def test_feature_buttons_use_real_labels_and_handlers():
    index_html = _read('index.html')
    chair_html = _read('chair.html')
    delegate_html = _read('delegate.html')

    _assert_control(index_html, 'showCreateSessionModal()', 'Create New MUN Session', 'index.html')
    _assert_control(index_html, 'createSession()', 'Create Session', 'index.html')
    _assert_control(index_html, 'saveMyDelegate()', 'Save My Info', 'index.html')
    _assert_control(index_html, 'generateSpeech()', 'Generate Speech', 'index.html')
    _assert_control(index_html, 'createNewNote()', 'New Note', 'index.html')
    _assert_control(index_html, 'saveNote()', 'Save', 'index.html')
    _assert_control(index_html, 'searchBook()', 'Search', 'index.html')

    _assert_control(chair_html, 'setupRoom()', 'Create Room', 'chair.html')
    _assert_control(chair_html, 'startRollCall()', 'Start Roll Call', 'chair.html')
    _assert_control(chair_html, 'startRollCallBtn()', 'Roll Call', 'chair.html')
    _assert_control(chair_html, 'openGSL()', 'Open GSL', 'chair.html')
    _assert_control(chair_html, 'startModCaucus()', 'Start Mod Caucus', 'chair.html')
    _assert_control(chair_html, 'startVoting()', 'Open Voting', 'chair.html')

    _assert_control(delegate_html, 'joinRoom()', 'Join Room', 'delegate.html')
    _assert_control(delegate_html, 'proposeMotion()', 'Propose Motion', 'delegate.html')
    _assert_control(delegate_html, 'submitMotion()', 'Propose', 'delegate.html')
    _assert_control(delegate_html, 'raisePoint()', 'Raise Point', 'delegate.html')
    _assert_control(delegate_html, 'submitPoint()', 'Raise Point', 'delegate.html')
    _assert_control(delegate_html, 'submitWorkingPaper()', 'Submit Working Paper', 'delegate.html')
    _assert_control(delegate_html, 'submitWP()', 'Submit', 'delegate.html')


def test_clear_room_button_is_bound():
    chair_html = _read('chair.html')
    chair_js = _read('chair.js')
    assert 'id="clear-room-btn"' in chair_html, 'missing id: clear-room-btn'
    assert "getElementById('clear-room-btn')" in chair_js, 'missing binding: clear-room-btn'
    assert 'clear-room-btn' in chair_js


def test_live_mun_widget_ids_exist_in_index():
    index_html = _read('index.html')
    for element_id in LIVE_MUN_IDS:
        assert re.search(
            rf'''\bid\s*=\s*["']{re.escape(element_id)}["']''',
            index_html,
        ), f'missing id: {element_id}'


def _top_level_lexical_names(source):
    """Names bound with const, let, or class at brace depth 0.

    Classic scripts on one page share a global lexical scope. A repeated
    top-level const is a SyntaxError and the later file never runs.
    """
    names = []
    i = 0
    length = len(source)
    depth = 0
    while i < length:
        char = source[i]
        if char in ' \t\r\n':
            i += 1
            continue
        if char == '/' and i + 1 < length and source[i + 1] == '/':
            newline = source.find('\n', i)
            i = length if newline < 0 else newline + 1
            continue
        if char == '/' and i + 1 < length and source[i + 1] == '*':
            end = source.find('*/', i + 2)
            i = length if end < 0 else end + 2
            continue
        if char in ('"', "'", '`'):
            quote = char
            i += 1
            while i < length:
                if source[i] == '\\':
                    i += 2
                    continue
                if source[i] == quote:
                    i += 1
                    break
                i += 1
            continue
        if char == '{':
            depth += 1
            i += 1
            continue
        if char == '}':
            depth = max(0, depth - 1)
            i += 1
            continue
        if depth == 0 and (char.isalpha() or char in '_$'):
            end = i + 1
            while end < length and (source[end].isalnum() or source[end] in '_$'):
                end += 1
            word = source[i:end]
            if word in ('const', 'let', 'class'):
                cursor = end
                while cursor < length and source[cursor] in ' \t':
                    cursor += 1
                name_end = cursor
                while name_end < length and (source[name_end].isalnum() or source[name_end] in '_$'):
                    name_end += 1
                if name_end > cursor:
                    names.append(source[cursor:name_end])
            i = end
            continue
        i += 1
    return names


def test_page_scripts_do_not_reuse_top_level_bindings():
    for page, scripts in PAGE_SCRIPTS.items():
        seen = {}
        for script in scripts:
            for name in _top_level_lexical_names(_read(script)):
                assert name not in seen, (
                    f'{page}: {script} redeclares top-level {name}, '
                    f'already declared in {seen[name]}'
                )
                seen[name] = script


def test_client_widgets_script():
    proc = subprocess.run(
        ['node', 'smoke_tests/client_widgets.mjs'],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0, proc.stdout + '\n' + proc.stderr
    assert 'SMOKE_OK' in proc.stdout
