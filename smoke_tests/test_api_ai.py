"""Smoke tests for AI HTTP routes with no provider configured.

A short explanation string from the model is a valid success payload.
Missing inputs must stay HTTP 400. HTTP 500 is never acceptable.
"""
import ast
import io
import os
import sys

import pytest

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
NOTES_DIR = os.path.join(ROOT, "data", "notes")

COUNTRY = "France"
TOPIC = "Climate"
COMMITTEE = "UNEP"
OTHER_COUNTRY = "Germany"
SPEECH = (
    "Honorable chair, France calls for binding climate targets "
    "and immediate support for the most affected states."
)
CRISIS = "Severe coastal flooding after extreme rainfall."


def _conftest_defines_flask_client():
    path = os.path.join(os.path.dirname(__file__), "conftest.py")
    if not os.path.isfile(path):
        return False
    try:
        tree = ast.parse(open(path, encoding="utf-8").read())
    except SyntaxError:
        return False
    return any(
        isinstance(node, ast.FunctionDef) and node.name == "flask_client"
        for node in ast.walk(tree)
    )


def _assert_http(response, expected, route):
    text = response.get_data(as_text=True)
    assert response.status_code != 500, f"{route} returned HTTP 500: {text[:1200]}"
    assert response.status_code == expected, (
        f"{route} returned {response.status_code}, expected {expected}: {text[:1200]}"
    )


def _json_object(response, route):
    body = response.get_json(silent=True)
    assert isinstance(body, dict) and body, (
        f"{route} expected a non-empty JSON object, got {response.get_data(as_text=True)[:1200]}"
    )
    return body


def _assert_text(body, field):
    value = body[field]
    assert isinstance(value, str) and value.strip(), (
        f"{field} must be a non-empty string, got {value!r}"
    )
    return value


def _assert_str_list(body, field):
    value = body[field]
    assert isinstance(value, list), f"{field} must be a list, got {type(value).__name__}"
    for item in value:
        assert isinstance(item, str), f"{field} entries must be strings, got {item!r}"
    return value


def _note_files():
    if not os.path.isdir(NOTES_DIR):
        return set()
    return {name for name in os.listdir(NOTES_DIR) if name.endswith(".json")}


def _note_id_from(item):
    if isinstance(item, str) and item.strip():
        return item.strip()
    if isinstance(item, dict):
        note_id = item.get("id")
        if isinstance(note_id, str) and note_id.strip():
            return note_id.strip()
    raise AssertionError(f"note entry has no id: {item!r}")


def _remove_note_files(note_ids):
    for note_id in note_ids:
        path = os.path.join(NOTES_DIR, f"{note_id}.json")
        if os.path.isfile(path):
            os.remove(path)
        data_root = os.path.join(ROOT, "data")
        if not os.path.isdir(data_root):
            continue
        target = f"{note_id}.json"
        for dirpath, _, filenames in os.walk(data_root):
            if target in filenames:
                os.remove(os.path.join(dirpath, target))


def _delete_notes(client, note_ids):
    for note_id in note_ids:
        client.delete(f"/api/notes/{note_id}")
    _remove_note_files(note_ids)
    for note_id in note_ids:
        leftover = os.path.join(NOTES_DIR, f"{note_id}.json")
        assert not os.path.exists(leftover), f"note file still present: {leftover}"


def _assert_sse(response, route):
    text = response.get_data(as_text=True)
    _assert_http(response, 200, route)
    assert response.mimetype == "text/event-stream", (
        f"{route} mimetype {response.mimetype!r}, body {text[:500]}"
    )
    assert "data:" in text, f"{route} SSE body missing data: {text[:500]}"
    assert "Traceback" not in text, f"{route} SSE body contains Traceback: {text[:1200]}"
    assert "KeyError" not in text, f"{route} SSE body contains KeyError: {text[:1200]}"


if not _conftest_defines_flask_client():

    @pytest.fixture(scope="module")
    def flask_client():
        os.chdir(ROOT)
        backend_dir = os.path.join(ROOT, "backend")
        if backend_dir not in sys.path:
            sys.path.insert(0, backend_dir)
        import app as mun

        mun.app.config["TESTING"] = True
        mun.app.config["PROPAGATE_EXCEPTIONS"] = False
        with mun.app.test_client() as client:
            yield client


def test_research_poi(flask_client):
    route = "/api/research/poi"
    response = flask_client.post(
        route,
        json={"country": COUNTRY, "topic": TOPIC, "target_country": OTHER_COUNTRY},
    )
    _assert_http(response, 200, route)
    body = _json_object(response, route)
    _assert_str_list(body, "questions")
    _assert_text(body, "formatted_output")
    assert body["country"] == COUNTRY
    assert body["topic"] == TOPIC


def test_research_poi_empty_country(flask_client):
    route = "/api/research/poi"
    response = flask_client.post(
        route,
        json={"country": "", "topic": TOPIC, "target_country": OTHER_COUNTRY},
    )
    _assert_http(response, 400, route)


def test_research_foreign_policy(flask_client):
    route = "/api/research/foreign-policy"
    response = flask_client.post(route, json={"country": COUNTRY, "topic": TOPIC})
    _assert_http(response, 200, route)
    body = _json_object(response, route)
    _assert_text(body, "policy")


def test_research_foreign_policy_missing_topic(flask_client):
    route = "/api/research/foreign-policy"
    response = flask_client.post(route, json={"country": COUNTRY})
    _assert_http(response, 400, route)


def test_research_modcaucus(flask_client):
    route = "/api/research/modcaucus"
    response = flask_client.post(
        route, json={"agenda": TOPIC, "committee": COMMITTEE}
    )
    _assert_http(response, 200, route)
    body = _json_object(response, route)
    _assert_str_list(body, "topics")
    _assert_text(body, "formatted_output")


def test_research_modcaucus_missing_agenda(flask_client):
    route = "/api/research/modcaucus"
    response = flask_client.post(route, json={"committee": COMMITTEE})
    _assert_http(response, 400, route)


def test_research_country_profile(flask_client):
    route = "/api/research/country-profile"
    response = flask_client.post(route, json={"country": COUNTRY, "topic": TOPIC})
    _assert_http(response, 200, route)
    body = _json_object(response, route)
    _assert_text(body, "profile")


def test_research_country_profile_missing_country(flask_client):
    route = "/api/research/country-profile"
    response = flask_client.post(route, json={"topic": TOPIC})
    _assert_http(response, 400, route)


def test_research_resolution_builder(flask_client):
    route = "/api/research/resolution-builder"
    response = flask_client.post(
        route, json={"country": COUNTRY, "topic": TOPIC, "committee": COMMITTEE}
    )
    _assert_http(response, 200, route)
    body = _json_object(response, route)
    _assert_text(body, "resolution")


def test_research_resolution_builder_missing_topic(flask_client):
    route = "/api/research/resolution-builder"
    response = flask_client.post(
        route, json={"country": COUNTRY, "committee": COMMITTEE}
    )
    _assert_http(response, 400, route)


def test_research_crisis_response(flask_client):
    route = "/api/research/crisis-response"
    response = flask_client.post(route, json={"country": COUNTRY, "crisis": CRISIS})
    _assert_http(response, 200, route)
    body = _json_object(response, route)
    _assert_text(body, "response")


def test_research_crisis_response_missing_crisis(flask_client):
    route = "/api/research/crisis-response"
    response = flask_client.post(route, json={"country": COUNTRY})
    _assert_http(response, 400, route)


def test_research_debate_prep(flask_client):
    route = "/api/research/debate-prep"
    response = flask_client.post(
        route,
        json={
            "my_country": COUNTRY,
            "opponent_country": OTHER_COUNTRY,
            "topic": TOPIC,
        },
    )
    _assert_http(response, 200, route)
    body = _json_object(response, route)
    _assert_text(body, "preparation")


def test_research_debate_prep_missing_topic(flask_client):
    route = "/api/research/debate-prep"
    response = flask_client.post(
        route,
        json={"my_country": COUNTRY, "opponent_country": OTHER_COUNTRY},
    )
    _assert_http(response, 400, route)


def test_research_allies(flask_client):
    route = "/api/research/allies"
    response = flask_client.post(route, json={"country": COUNTRY, "topic": TOPIC})
    _assert_http(response, 200, route)
    body = _json_object(response, route)
    _assert_text(body, "allies")


def test_research_opposition(flask_client):
    route = "/api/research/opposition"
    response = flask_client.post(route, json={"country": COUNTRY, "topic": TOPIC})
    _assert_http(response, 200, route)
    body = _json_object(response, route)
    _assert_text(body, "opposition")


def test_research_comprehensive(flask_client):
    route = "/api/research/comprehensive"
    before = _note_files()
    note_ids = []
    try:
        response = flask_client.post(
            route,
            json={"country": COUNTRY, "topic": TOPIC, "committee": COMMITTEE},
        )
        _assert_http(response, 200, route)
        body = _json_object(response, route)
        notes = body["notes_created"]
        assert isinstance(notes, list) and notes, "notes_created must be a non-empty list"
        note_ids = [_note_id_from(item) for item in notes]
        _assert_text(body, "message")
    finally:
        extra = []
        for name in _note_files() - before:
            extra.append(name[: -len(".json")])
        _delete_notes(flask_client, list(dict.fromkeys(note_ids + extra)))


def test_research_comprehensive_missing_country(flask_client):
    route = "/api/research/comprehensive"
    before = _note_files()
    response = flask_client.post(
        route, json={"topic": TOPIC, "committee": COMMITTEE}
    )
    _assert_http(response, 400, route)
    assert _note_files() == before


def test_research_parallel(flask_client):
    route = "/api/research/parallel"
    response = flask_client.post(
        route,
        json={
            "country": COUNTRY,
            "topic": TOPIC,
            "tasks": ["research", "allies", "opposition"],
        },
    )
    _assert_http(response, 200, route)
    _json_object(response, route)


def test_research_parallel_missing_topic(flask_client):
    route = "/api/research/parallel"
    response = flask_client.post(
        route,
        json={"country": COUNTRY, "tasks": ["research", "allies", "opposition"]},
    )
    _assert_http(response, 400, route)


def test_research_comprehensive_stream(flask_client):
    route = "/api/research/comprehensive-stream"
    response = flask_client.post(
        route,
        json={"country": COUNTRY, "topic": TOPIC, "committee": COMMITTEE},
    )
    _assert_sse(response, route)


def test_research_crisis_stream(flask_client):
    route = "/api/research/crisis-stream"
    response = flask_client.post(route, json={"country": COUNTRY, "crisis": CRISIS})
    _assert_sse(response, route)


def test_research_debate_mastery_stream(flask_client):
    route = "/api/research/debate-mastery-stream"
    response = flask_client.post(
        route,
        json={
            "country": COUNTRY,
            "topic": TOPIC,
            "opponent_country": OTHER_COUNTRY,
        },
    )
    _assert_sse(response, route)


def test_research_debate_mastery_stream_missing_topic(flask_client):
    route = "/api/research/debate-mastery-stream"
    response = flask_client.post(
        route, json={"country": COUNTRY, "opponent_country": OTHER_COUNTRY}
    )
    _assert_http(response, 400, route)


def test_live_auto_notes_process_stream(flask_client):
    route = "/api/live-auto-notes/process-stream"
    response = flask_client.post(
        route,
        json={
            "transcript_chunk": (
                "France will vote for the climate resolution and support the amendment."
            ),
            "speaker": COUNTRY,
            "timestamp": "00:01:00",
        },
    )
    _assert_sse(response, route)


def test_live_auto_notes_process_stream_missing_transcript(flask_client):
    route = "/api/live-auto-notes/process-stream"
    response = flask_client.post(
        route, json={"speaker": COUNTRY, "timestamp": "00:01:00"}
    )
    _assert_http(response, 400, route)


def test_notes_analyze(flask_client):
    before = _note_files()
    note_ids = []
    try:
        created = flask_client.post(
            "/api/notes",
            json={"title": "France climate note", "content": SPEECH},
        )
        _assert_http(created, 201, "POST /api/notes")
        note_id = _note_id_from(_json_object(created, "POST /api/notes"))
        note_ids.append(note_id)
        route = f"/api/notes/{note_id}/analyze"
        response = flask_client.post(route)
        _assert_http(response, 200, route)
        _json_object(response, route)
    finally:
        extra = [name[: -len(".json")] for name in _note_files() - before]
        _delete_notes(flask_client, list(dict.fromkeys(note_ids + extra)))


def test_speech_rate_grammar(flask_client):
    route = "/api/speech/rate-grammar"
    response = flask_client.post(route, json={"speech_text": SPEECH})
    _assert_http(response, 200, route)
    _json_object(response, route)


def test_speech_rate_grammar_missing_speech_text(flask_client):
    route = "/api/speech/rate-grammar"
    response = flask_client.post(route, json={})
    _assert_http(response, 400, route)


def test_speech_rate_ethics(flask_client):
    route = "/api/speech/rate-ethics"
    response = flask_client.post(
        route, json={"speech_text": SPEECH, "country": COUNTRY}
    )
    _assert_http(response, 200, route)
    _json_object(response, route)


def test_speech_rate_impact(flask_client):
    route = "/api/speech/rate-impact"
    response = flask_client.post(
        route,
        json={"speech_text": SPEECH, "topic": TOPIC, "committee": COMMITTEE},
    )
    _assert_http(response, 200, route)
    _json_object(response, route)


def test_speech_rate_comprehensive(flask_client):
    route = "/api/speech/rate-comprehensive"
    response = flask_client.post(
        route,
        json={
            "speech_text": SPEECH,
            "country": COUNTRY,
            "topic": TOPIC,
            "committee": COMMITTEE,
        },
    )
    _assert_http(response, 200, route)
    _json_object(response, route)


def test_speech_summary_and_rewrite(flask_client):
    route = "/api/speech/summary-and-rewrite"
    response = flask_client.post(
        route, json={"speech_text": SPEECH, "country": COUNTRY, "topic": TOPIC}
    )
    _assert_http(response, 200, route)
    _json_object(response, route)


def test_speech_summary_and_rewrite_missing_speech_text(flask_client):
    route = "/api/speech/summary-and-rewrite"
    response = flask_client.post(
        route, json={"country": COUNTRY, "topic": TOPIC}
    )
    _assert_http(response, 400, route)


def test_chit_poi(flask_client):
    route = "/api/chit/poi"
    response = flask_client.post(
        route,
        json={
            "to_country": OTHER_COUNTRY,
            "question": "What is your emissions target?",
            "topic": TOPIC,
            "my_country": COUNTRY,
        },
    )
    _assert_http(response, 200, route)
    body = _json_object(response, route)
    _assert_text(body, "chit")


def test_chit_poi_missing_to_country(flask_client):
    route = "/api/chit/poi"
    response = flask_client.post(
        route,
        json={
            "question": "What is your emissions target?",
            "topic": TOPIC,
            "my_country": COUNTRY,
        },
    )
    _assert_http(response, 400, route)


def test_chit_lobby(flask_client):
    route = "/api/chit/lobby"
    response = flask_client.post(
        route,
        json={
            "to_country": OTHER_COUNTRY,
            "purpose": "Discuss a joint climate clause",
            "my_country": COUNTRY,
            "topic": TOPIC,
        },
    )
    _assert_http(response, 200, route)
    body = _json_object(response, route)
    _assert_text(body, "chit")


def test_chit_general(flask_client):
    route = "/api/chit/general"
    response = flask_client.post(
        route,
        json={
            "to_country": OTHER_COUNTRY,
            "message": "Request a meeting on climate language",
            "my_country": COUNTRY,
            "tone": "professional",
        },
    )
    _assert_http(response, 200, route)
    body = _json_object(response, route)
    _assert_text(body, "chit")


def test_chit_general_missing_message(flask_client):
    route = "/api/chit/general"
    response = flask_client.post(
        route,
        json={
            "to_country": OTHER_COUNTRY,
            "my_country": COUNTRY,
            "tone": "professional",
        },
    )
    _assert_http(response, 400, route)


def test_chit_directive(flask_client):
    route = "/api/chit/directive"
    response = flask_client.post(
        route,
        json={
            "to_country": OTHER_COUNTRY,
            "directive": "Support the climate resolution",
            "my_country": COUNTRY,
            "urgency": "normal",
        },
    )
    _assert_http(response, 200, route)
    body = _json_object(response, route)
    _assert_text(body, "chit")


def test_chit_respond(flask_client):
    route = "/api/chit/respond"
    response = flask_client.post(
        route,
        json={
            "original_chit": "France requests a meeting on climate.",
            "response_type": "positive",
            "my_country": COUNTRY,
        },
    )
    _assert_http(response, 200, route)
    body = _json_object(response, route)
    _assert_text(body, "chit")


def test_chit_respond_missing_original_chit(flask_client):
    route = "/api/chit/respond"
    response = flask_client.post(
        route, json={"response_type": "positive", "my_country": COUNTRY}
    )
    _assert_http(response, 400, route)


def test_transcribe_missing_file(flask_client):
    route = "/api/transcribe"
    response = flask_client.post(route, data={})
    _assert_http(response, 400, route)


def test_transcribe_audio_openai_unavailable(flask_client):
    route = "/api/transcribe"
    response = flask_client.post(
        route,
        data={"audio": (io.BytesIO(b"RIFF\x00\x00\x00\x00WAVE"), "clip.wav")},
    )
    _assert_http(response, 503, route)
    body = _json_object(response, route)
    _assert_text(body, "error")


def test_notes_save_research(flask_client):
    route = "/api/notes/save-research"
    before = _note_files()
    note_ids = []
    try:
        response = flask_client.post(
            route,
            json={
                "title": "France climate research",
                "content": "Sample research content on climate.",
                "folder": "research",
            },
        )
        _assert_http(response, 201, route)
        body = _json_object(response, route)
        note_ids = [_assert_text(body, "id")]
    finally:
        extra = [name[: -len(".json")] for name in _note_files() - before]
        _delete_notes(flask_client, list(dict.fromkeys(note_ids + extra)))
