"""Smoke-test fixtures. Load the real Flask app; do not mock AI."""

import os
import sys

import pytest

_WORKSPACE = "/workspace"
_BACKEND = "/workspace/backend"


def _prepare_import_path():
    os.chdir(_WORKSPACE)
    if _BACKEND not in sys.path:
        sys.path.insert(0, _BACKEND)


_prepare_import_path()


@pytest.fixture(scope="session")
def mun():
    """Imported backend app module (app, socketio, and helpers)."""
    _prepare_import_path()
    import app as app_module

    return app_module


@pytest.fixture
def flask_client(mun):
    return mun.app.test_client()
