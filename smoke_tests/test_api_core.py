"""Smoke tests for the non-AI MUNvare product API."""

import json
import shutil
import threading
import uuid
from pathlib import Path


def unique(label):
    return f"smoke-{label}-{uuid.uuid4().hex[:12]}"


def assert_status(response, status_code):
    assert response.status_code == status_code, response.get_data(as_text=True)[:500]


def ids_of(payload):
    assert isinstance(payload, list), payload
    return [item.get("id") for item in payload]


def create_session(client, name=None):
    payload = {
        "name": name or unique("session"),
        "description": unique("desc"),
        "dates": "2026-10-25 to 2026-10-27",
    }
    response = client.post("/api/sessions", json=payload)
    assert_status(response, 201)
    body = response.get_json()
    assert body["id"]
    assert body["name"] == payload["name"]
    assert body["description"] == payload["description"]
    assert body["dates"] == payload["dates"]
    return body


def delete_session(client, session_id):
    if session_id:
        client.delete(f"/api/sessions/{session_id}")


def snapshot_config(mun):
    path = Path(mun.config_manager.config_file)
    return path, path.read_bytes()


def restore_config(mun, path, raw):
    path.write_bytes(raw)
    mun.config_manager.config = json.loads(raw.decode("utf-8"))


def snapshot_folders(mun):
    path = Path(mun.notes_manager.folders_file)
    raw = path.read_bytes() if path.exists() else None
    return path, raw


def restore_folders(mun, path, raw):
    if raw is None:
        return
    path.write_bytes(raw)
    mun.notes_manager.folders = json.loads(raw.decode("utf-8"))


def remove_global_note(mun, note_id):
    if not note_id:
        return
    path = Path(mun.NOTES_DIR) / f"{note_id}.json"
    if path.is_file():
        path.unlink()


def delete_global_note(client, mun, note_id):
    if not note_id:
        return
    client.delete(f"/api/notes/{note_id}")
    remove_global_note(mun, note_id)


def create_global_note(client, title, content="Smoke note content"):
    response = client.post("/api/notes", json={"title": title, "content": content})
    assert_status(response, 201)
    body = response.get_json()
    assert body["id"]
    assert body["title"] == title
    return body


def remove_chat_files(mun, chat_id, session_ids=()):
    if not chat_id:
        return
    name = f"{chat_id}.json"
    candidates = [Path(mun.chat_manager.chats_dir) / name]
    root = Path(mun.session_manager.data_dir)
    for session_id in session_ids:
        if session_id:
            candidates.append(root / session_id / "chats" / name)
    for path in candidates:
        if path.is_file():
            path.unlink()


def remove_speech_files(mun, speech_id, session_ids=()):
    if not speech_id:
        return
    name = f"{speech_id}.json"
    candidates = [Path(mun.SPEECHES_DIR) / name]
    root = Path(mun.session_manager.data_dir)
    for session_id in session_ids:
        if session_id:
            candidates.append(root / session_id / "speeches" / name)
    for path in candidates:
        if path.is_file():
            path.unlink()


def remove_unknown_session_dir(mun, session_id):
    if not session_id:
        return
    stray = Path(mun.session_manager.data_dir) / session_id
    if stray.exists():
        shutil.rmtree(stray)


def test_health_and_pages(flask_client):
    health = flask_client.get("/api/health")
    assert_status(health, 200)
    assert health.get_json()["status"] == "healthy"

    home = flask_client.get("/")
    assert_status(home, 200)
    html = home.get_data(as_text=True)
    assert "Welcome to MUNvare" in html
    assert "Create New MUN Session" in html

    chair = flask_client.get("/chair")
    assert_status(chair, 200)
    chair_html = chair.get_data(as_text=True)
    assert "Chair Interface" in chair_html
    assert "setupRoom" in chair_html

    delegate = flask_client.get("/delegate")
    assert_status(delegate, 200)
    delegate_html = delegate.get_data(as_text=True)
    assert "Delegate Interface" in delegate_html
    assert "joinRoom" in delegate_html

    for path in (
        "/styles.css",
        "/app.js",
        "/chair.js",
        "/delegate.js",
        "/chair.css",
        "/delegate.css",
    ):
        asset = flask_client.get(path)
        assert asset.status_code == 200, path
        assert asset.data, path


def test_sessions_create_update_and_delete(flask_client):
    missing = flask_client.post(
        "/api/sessions",
        json={"description": "missing name", "dates": "2026-10-25"},
    )
    assert_status(missing, 400)

    session_id = None
    try:
        created = create_session(flask_client)
        session_id = created["id"]

        listed = flask_client.get("/api/sessions")
        assert_status(listed, 200)
        assert session_id in ids_of(listed.get_json())

        fetched = flask_client.get(f"/api/sessions/{session_id}")
        assert_status(fetched, 200)
        assert fetched.get_json()["id"] == session_id
        assert fetched.get_json()["name"] == created["name"]

        renamed = unique("session-renamed")
        updated = flask_client.put(
            f"/api/sessions/{session_id}",
            json={"name": renamed},
        )
        assert_status(updated, 200)
        assert updated.get_json()["name"] == renamed

        active = flask_client.get("/api/sessions/active")
        assert_status(active, 200)
        assert session_id in ids_of(active.get_json())

        deleted = flask_client.delete(f"/api/sessions/{session_id}")
        assert_status(deleted, 200)
        gone = flask_client.get(f"/api/sessions/{session_id}")
        assert_status(gone, 404)
        session_id = None

        missing_session = flask_client.get(f"/api/sessions/{uuid.uuid4()}")
        assert_status(missing_session, 404)
    finally:
        delete_session(flask_client, session_id)


def test_sessions_end_summary_import_detach(flask_client):
    source_id = None
    target_id = None
    try:
        source = create_session(flask_client)
        source_id = source["id"]

        active = flask_client.get("/api/sessions/active")
        assert_status(active, 200)
        assert source_id in ids_of(active.get_json())

        ended = flask_client.post(f"/api/sessions/{source_id}/end")
        assert_status(ended, 200)
        ended_body = ended.get_json()
        assert isinstance(ended_body.get("summary"), str) and ended_body["summary"].strip()
        assert isinstance(ended_body.get("stats"), dict)

        ended_list = flask_client.get("/api/sessions/ended")
        assert_status(ended_list, 200)
        assert source_id in ids_of(ended_list.get_json())

        summary = flask_client.get(f"/api/sessions/{source_id}/summary")
        assert_status(summary, 200)
        summary_body = summary.get_json()
        assert isinstance(summary_body.get("summary"), str) and summary_body["summary"].strip()
        assert summary_body.get("compressed_memory")

        target = create_session(flask_client)
        target_id = target["id"]
        imported = flask_client.post(f"/api/sessions/{target_id}/import/{source_id}")
        assert_status(imported, 200)

        detached = flask_client.post(f"/api/sessions/{target_id}/detach/{source_id}")
        assert_status(detached, 200)

        for session_id in (source_id, target_id):
            deleted = flask_client.delete(f"/api/sessions/{session_id}")
            assert_status(deleted, 200)
        source_id = None
        target_id = None
    finally:
        delete_session(flask_client, source_id)
        delete_session(flask_client, target_id)


def test_notes_crud_and_folder_move(flask_client, mun):
    note_id = None
    try:
        listed = flask_client.get("/api/notes")
        assert_status(listed, 200)
        assert isinstance(listed.get_json(), list)

        title = unique("note")
        created = create_global_note(flask_client, title, content="Smoke note body")
        note_id = created["id"]
        assert note_id in ids_of(flask_client.get("/api/notes").get_json())

        fetched = flask_client.get(f"/api/notes/{note_id}")
        assert_status(fetched, 200)
        assert fetched.get_json()["title"] == title
        assert fetched.get_json()["content"] == "Smoke note body"

        renamed = unique("note-updated")
        updated = flask_client.put(
            f"/api/notes/{note_id}",
            json={"title": renamed, "content": "Updated smoke body"},
        )
        assert_status(updated, 200)
        assert updated.get_json()["title"] == renamed
        assert updated.get_json()["content"] == "Updated smoke body"

        moved = flask_client.post(
            f"/api/notes/{note_id}/move-to-folder",
            json={"folder_id": "research"},
        )
        assert_status(moved, 200)
        assert moved.get_json()["folder"] == "research"

        deleted = flask_client.delete(f"/api/notes/{note_id}")
        assert_status(deleted, 200)
        missing = flask_client.get(f"/api/notes/{note_id}")
        assert_status(missing, 404)
        note_id = None
    finally:
        delete_global_note(flask_client, mun, note_id)


def test_note_export_txt_without_session(flask_client, mun):
    title = unique("export-txt")
    note_id = None
    try:
        note_id = create_global_note(flask_client, title)["id"]
        exported = flask_client.get(f"/api/notes/{note_id}/export/txt")
        assert_status(exported, 200)
        assert "text/plain" in exported.content_type
        assert title in exported.get_data(as_text=True)
    finally:
        delete_global_note(flask_client, mun, note_id)


def test_note_export_pdf_without_session(flask_client, mun):
    title = unique("export-pdf")
    note_id = None
    try:
        note_id = create_global_note(flask_client, title)["id"]
        exported = flask_client.get(f"/api/notes/{note_id}/export/pdf")
        assert_status(exported, 200)
        assert "pdf" in exported.content_type.lower()
    finally:
        delete_global_note(flask_client, mun, note_id)


def test_notes_export_all_txt_without_session(flask_client, mun):
    title = unique("export-all")
    note_id = None
    try:
        note_id = create_global_note(flask_client, title)["id"]
        exported = flask_client.get("/api/notes/export-all/txt")
        assert_status(exported, 200)
        assert "text/plain" in exported.content_type
        assert title in exported.get_data(as_text=True)
    finally:
        delete_global_note(flask_client, mun, note_id)


def test_notes_unknown_session_header_returns_404(flask_client, mun):
    unknown_id = uuid.uuid4().hex
    note_id = None
    try:
        response = flask_client.post(
            "/api/notes",
            json={"title": unique("unknown-session-note"), "content": "nope"},
            headers={"X-Session-Id": unknown_id},
        )
        payload = response.get_json(silent=True)
        if isinstance(payload, dict):
            note_id = payload.get("id")
        assert_status(response, 404)
        assert isinstance(payload, dict) and payload.get("error")
    finally:
        remove_global_note(mun, note_id)
        remove_unknown_session_dir(mun, unknown_id)


def test_notes_are_isolated_by_session_header(flask_client, mun):
    session_a = None
    session_b = None
    note_id = None
    try:
        session_a = create_session(flask_client)["id"]
        session_b = create_session(flask_client)["id"]
        title = unique("session-note")
        created = flask_client.post(
            "/api/notes",
            json={"title": title, "content": "visible only in session A"},
            headers={"X-Session-Id": session_a},
        )
        assert_status(created, 201)
        note_id = created.get_json()["id"]

        list_a = flask_client.get("/api/notes", headers={"X-Session-Id": session_a})
        assert_status(list_a, 200)
        assert note_id in ids_of(list_a.get_json())

        list_b = flask_client.get("/api/notes", headers={"X-Session-Id": session_b})
        assert_status(list_b, 200)
        assert note_id not in ids_of(list_b.get_json())

        list_global = flask_client.get("/api/notes")
        assert_status(list_global, 200)
        assert note_id not in ids_of(list_global.get_json())

        fetched_a = flask_client.get(
            f"/api/notes/{note_id}",
            headers={"X-Session-Id": session_a},
        )
        assert_status(fetched_a, 200)
        assert fetched_a.get_json()["title"] == title

        fetched_b = flask_client.get(
            f"/api/notes/{note_id}",
            headers={"X-Session-Id": session_b},
        )
        assert_status(fetched_b, 404)
    finally:
        remove_global_note(mun, note_id)
        delete_session(flask_client, session_a)
        delete_session(flask_client, session_b)


def test_notes_v2_folders_and_templates(flask_client, mun):
    folders_path, folders_raw = snapshot_folders(mun)
    notes_dir = Path(mun.notes_manager.notes_dir)
    before = {path.name for path in notes_dir.glob("*.json")}
    try:
        folders = flask_client.get("/api/notes-v2/folders")
        assert_status(folders, 200)
        folder_list = folders.get_json()
        assert isinstance(folder_list, list) and folder_list
        assert all(folder.get("id") for folder in folder_list)

        folder_name = unique("folder")
        created_folder = flask_client.post(
            "/api/notes-v2/folders",
            json={"name": folder_name},
        )
        assert_status(created_folder, 201)
        created_body = created_folder.get_json()
        assert created_body["id"]
        assert created_body["name"] == folder_name

        templates = flask_client.get("/api/notes-v2/templates")
        assert_status(templates, 200)
        assert "country_research" in ids_of(templates.get_json())

        from_template = flask_client.post(
            "/api/notes-v2/from-template",
            json={"template_id": "country_research", "title": "Smoke template"},
        )
        assert_status(from_template, 201)
        note = from_template.get_json()
        assert note["id"]
        assert note["title"] == "Smoke template"

        bad = flask_client.post(
            "/api/notes-v2/from-template",
            json={"template_id": unique("missing-template"), "title": "Smoke template"},
        )
        assert_status(bad, 404)
    finally:
        restore_folders(mun, folders_path, folders_raw)
        for path in notes_dir.glob("*.json"):
            if path.name not in before and path.name != "folders.json":
                path.unlink()


def test_config_delegate_and_committee(flask_client, mun):
    path, raw = snapshot_config(mun)
    try:
        current = flask_client.get("/api/config")
        assert_status(current, 200)
        config = current.get_json()
        assert "my_delegate" in config
        assert "other_delegates" in config
        assert "committee_info" in config

        country = unique("country")
        updated = flask_client.post(
            "/api/config/delegate",
            json={
                "country": country,
                "committee": "UNEP",
                "agenda": "Climate",
                "portfolio": "Environment",
            },
        )
        assert_status(updated, 200)
        assert updated.get_json()["my_delegate"]["country"] == country

        added = flask_client.post(
            "/api/config/delegates",
            json={"country": unique("other-country"), "notes": "smoke delegate"},
        )
        assert_status(added, 201)
        delegate_id = added.get_json()["id"]
        assert delegate_id

        removed = flask_client.delete(f"/api/config/delegates/{delegate_id}")
        assert_status(removed, 200)

        committee = flask_client.post(
            "/api/config/committee",
            json={
                "committee": "UNEP",
                "agenda": "Climate finance",
                "study_guide": "https://example.test/guide",
                "position_paper_due": "2026-11-01",
            },
        )
        assert_status(committee, 200)
        info = committee.get_json()["committee_info"]
        assert info["committee"] == "UNEP"
        assert info["agenda"] == "Climate finance"
        assert info["study_guide"] == "https://example.test/guide"
        assert info["position_paper_due"] == "2026-11-01"
    finally:
        restore_config(mun, path, raw)


def test_config_delegate_does_not_leak_across_sessions(flask_client, mun):
    path, raw = snapshot_config(mun)
    session_a = None
    session_b = None
    try:
        session_a = create_session(flask_client)["id"]
        session_b = create_session(flask_client)["id"]
        before = flask_client.get("/api/config").get_json()
        country = unique("session-country")

        updated = flask_client.post(
            "/api/config/delegate",
            json={
                "country": country,
                "committee": "WHO",
                "agenda": "Health",
                "portfolio": "Public health",
            },
            headers={"X-Session-Id": session_a},
        )
        assert_status(updated, 200)

        global_config = flask_client.get("/api/config")
        assert_status(global_config, 200)
        global_body = global_config.get_json()
        assert global_body["my_delegate"] == before["my_delegate"]
        assert country not in json.dumps(global_body)

        other = flask_client.get("/api/config", headers={"X-Session-Id": session_b})
        assert_status(other, 200)
        assert country not in json.dumps(other.get_json())

        own = flask_client.get("/api/config", headers={"X-Session-Id": session_a})
        assert_status(own, 200)
        assert own.get_json()["my_delegate"]["country"] == country
    finally:
        delete_session(flask_client, session_a)
        delete_session(flask_client, session_b)
        restore_config(mun, path, raw)


def test_chats_create_send_and_delete(flask_client, mun):
    chat_id = None
    try:
        listed = flask_client.get("/api/chats")
        assert_status(listed, 200)
        assert isinstance(listed.get_json(), list)

        title = unique("chat")
        created = flask_client.post("/api/chats", json={"title": title})
        assert_status(created, 201)
        body = created.get_json()
        chat_id = body["id"]
        assert body["title"] == title

        fetched = flask_client.get(f"/api/chats/{chat_id}")
        assert_status(fetched, 200)
        assert fetched.get_json()["id"] == chat_id

        missing_message = flask_client.post("/api/chat", json={})
        assert_status(missing_message, 400)

        sent = flask_client.post(
            "/api/chat",
            json={"message": "Smoke test ping", "chat_id": chat_id},
        )
        assert_status(sent, 200)
        sent_body = sent.get_json()
        assert sent_body["chat_id"] == chat_id
        assert isinstance(sent_body.get("response"), str) and sent_body["response"].strip()

        deleted = flask_client.delete(f"/api/chats/{chat_id}")
        assert_status(deleted, 200)
        missing = flask_client.get(f"/api/chats/{chat_id}")
        assert_status(missing, 404)
        chat_id = None
    finally:
        if chat_id:
            flask_client.delete(f"/api/chats/{chat_id}")
            remove_chat_files(mun, chat_id)


def test_chats_are_isolated_by_session_header(flask_client, mun):
    session_a = None
    session_b = None
    chat_id = None
    try:
        session_a = create_session(flask_client)["id"]
        session_b = create_session(flask_client)["id"]
        created = flask_client.post(
            "/api/chats",
            json={"title": unique("session-chat")},
            headers={"X-Session-Id": session_a},
        )
        assert_status(created, 201)
        chat_id = created.get_json()["id"]

        list_a = flask_client.get("/api/chats", headers={"X-Session-Id": session_a})
        assert_status(list_a, 200)
        assert chat_id in ids_of(list_a.get_json())

        list_b = flask_client.get("/api/chats", headers={"X-Session-Id": session_b})
        assert_status(list_b, 200)
        assert chat_id not in ids_of(list_b.get_json())
    finally:
        if chat_id:
            flask_client.delete(f"/api/chats/{chat_id}", headers={"X-Session-Id": session_a})
            flask_client.delete(f"/api/chats/{chat_id}")
        remove_chat_files(mun, chat_id, [session_a, session_b])
        delete_session(flask_client, session_a)
        delete_session(flask_client, session_b)


def test_search_and_premade_notes(flask_client):
    missing = flask_client.post("/api/search", json={})
    assert_status(missing, 400)

    found = flask_client.post("/api/search", json={"query": "points of information"})
    assert_status(found, 200)
    body = found.get_json()
    assert body["query"] == "points of information"
    assert isinstance(body.get("results"), list) and body["results"]

    premade = flask_client.get("/api/premade-notes")
    assert_status(premade, 200)
    assert isinstance(premade.get_json(), list)

    absent = flask_client.get("/api/premade-notes/does-not-exist")
    assert_status(absent, 404)


def test_committee_flow_blocks_reorder_and_status(flask_client):
    flow_id = None
    try:
        templates = flask_client.get("/api/committee-flow/templates")
        assert_status(templates, 200)
        assert "gsl" in ids_of(templates.get_json())

        listed = flask_client.get("/api/committee-flow")
        assert_status(listed, 200)
        assert isinstance(listed.get_json(), list)

        name = unique("flow")
        created = flask_client.post(
            "/api/committee-flow",
            json={"name": name, "session_id": unique("flow-session")},
        )
        assert_status(created, 201)
        flow = created.get_json()
        flow_id = flow["id"]
        assert flow["name"] == name

        fetched = flask_client.get(f"/api/committee-flow/{flow_id}")
        assert_status(fetched, 200)
        assert fetched.get_json()["name"] == name

        renamed = unique("flow-renamed")
        updated = flask_client.put(
            f"/api/committee-flow/{flow_id}",
            json={"name": renamed},
        )
        assert_status(updated, 200)
        assert updated.get_json()["name"] == renamed

        first = flask_client.post(
            f"/api/committee-flow/{flow_id}/blocks",
            json={"type": "gsl", "data": {"speaker_time": 90}},
        )
        assert_status(first, 201)
        first_body = first.get_json()
        first_id = first_body["id"]
        assert first_id
        assert first_body["data"]["speaker_time"] == 90

        second = flask_client.post(
            f"/api/committee-flow/{flow_id}/blocks",
            json={"type": "unmoderated_caucus", "data": {"duration": 10}},
        )
        assert_status(second, 201)
        second_id = second.get_json()["id"]
        assert second_id

        reordered = flask_client.post(
            f"/api/committee-flow/{flow_id}/blocks/reorder",
            json={"block_order": [second_id, first_id]},
        )
        assert_status(reordered, 200)
        flow_after = flask_client.get(f"/api/committee-flow/{flow_id}")
        assert_status(flow_after, 200)
        order = [block["id"] for block in flow_after.get_json()["blocks"]]
        assert order == [second_id, first_id]

        edited = flask_client.put(
            f"/api/committee-flow/{flow_id}/blocks/{second_id}",
            json={"data": {"duration": 15, "purpose": "drafting"}},
        )
        assert_status(edited, 200)
        assert edited.get_json()["data"]["duration"] == 15

        started = flask_client.post(
            f"/api/committee-flow/{flow_id}/blocks/{second_id}/start"
        )
        assert_status(started, 200)
        assert started.get_json()["status"] == "active"

        noted = flask_client.post(
            f"/api/committee-flow/{flow_id}/blocks/{second_id}/notes",
            json={"note": "hello"},
        )
        assert_status(noted, 200)
        assert any(
            "hello" in (item.get("text") or "")
            for item in noted.get_json()["notes"]
        )

        completed = flask_client.post(
            f"/api/committee-flow/{flow_id}/blocks/{second_id}/complete"
        )
        assert_status(completed, 200)
        assert completed.get_json()["status"] == "completed"

        missing_type = flask_client.post(
            f"/api/committee-flow/{flow_id}/blocks",
            json={"data": {"speaker_time": 60}},
        )
        assert_status(missing_type, 400)

        missing_note = flask_client.post(
            f"/api/committee-flow/{flow_id}/blocks/{second_id}/notes",
            json={},
        )
        assert_status(missing_note, 400)

        removed_block = flask_client.delete(
            f"/api/committee-flow/{flow_id}/blocks/{first_id}"
        )
        assert_status(removed_block, 200)

        deleted = flask_client.delete(f"/api/committee-flow/{flow_id}")
        assert_status(deleted, 200)
        missing = flask_client.get(f"/api/committee-flow/{flow_id}")
        assert_status(missing, 404)
        flow_id = None
    finally:
        if flow_id:
            flask_client.delete(f"/api/committee-flow/{flow_id}")


def test_speech_generate_requires_country_and_returns_content(flask_client, mun):
    rejected = flask_client.post(
        "/api/speech/generate",
        json={
            "topic": "Climate",
            "committee": "UNEP",
            "stance": "support",
            "speech_type": "GSL",
        },
    )
    assert_status(rejected, 400)

    speech_id = None
    try:
        created = flask_client.post(
            "/api/speech/generate",
            json={
                "country": "France",
                "topic": "Climate",
                "committee": "UNEP",
                "stance": "support",
                "speech_type": "GSL",
            },
        )
        assert_status(created, 200)
        body = created.get_json()
        speech_id = body["id"]
        assert isinstance(body.get("content"), str) and body["content"].strip()
    finally:
        remove_speech_files(mun, speech_id)


def test_speeches_are_isolated_by_session_header(flask_client, mun):
    session_a = None
    session_b = None
    speech_id = None
    try:
        session_a = create_session(flask_client)["id"]
        session_b = create_session(flask_client)["id"]
        created = flask_client.post(
            "/api/speech/generate",
            json={
                "country": "France",
                "topic": "Climate",
                "committee": "UNEP",
                "stance": "support",
                "speech_type": "GSL",
            },
            headers={"X-Session-Id": session_a},
        )
        assert_status(created, 200)
        body = created.get_json()
        speech_id = body["id"]
        assert isinstance(body.get("content"), str) and body["content"].strip()

        listed_a = flask_client.get("/api/speeches", headers={"X-Session-Id": session_a})
        assert_status(listed_a, 200)
        assert speech_id in ids_of(listed_a.get_json())

        listed_b = flask_client.get("/api/speeches", headers={"X-Session-Id": session_b})
        assert_status(listed_b, 200)
        assert speech_id not in ids_of(listed_b.get_json())
    finally:
        remove_speech_files(mun, speech_id, [session_a, session_b])
        delete_session(flask_client, session_a)
        delete_session(flask_client, session_b)


def test_parallel_session_lookups_keep_the_notes_list(flask_client, mun):
    """Opening a session fires many /api calls at once. Each one used to rewrite
    sessions.json, and a reader could see an empty file and get 404."""
    session_id = None
    note_id = None
    try:
        session_id = create_session(flask_client)["id"]
        created = flask_client.post(
            "/api/notes",
            json={"title": "Parallel note", "content": "still listed"},
            headers={"X-Session-Id": session_id},
        )
        assert_status(created, 201)
        note_id = created.get_json()["id"]

        errors = []

        def read_notes():
            client = mun.app.test_client()
            for _ in range(12):
                response = client.get("/api/notes", headers={"X-Session-Id": session_id})
                if response.status_code != 200:
                    errors.append(response.get_data(as_text=True)[:200])
                    return
                payload = response.get_json()
                if not isinstance(payload, list) or note_id not in ids_of(payload):
                    errors.append(repr(payload)[:200])
                    return

        threads = [threading.Thread(target=read_notes) for _ in range(8)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()
        assert errors == []
    finally:
        delete_session(flask_client, session_id)
