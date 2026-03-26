"""Tests for WorkspaceManager functionality.

Tests are organized by feature and use both real filesystem and mocked approaches
where appropriate.
"""

import os
import shutil
from pathlib import Path
from unittest.mock import patch

import pytest

from ai_coding_agent.core.logger import get_logger
from ai_coding_agent.core.result import Err, Ok, is_err

logger = get_logger(__name__)


@pytest.fixture
def base_path():
    """Provide a temporary base path for tests."""
    path = "/tmp/test_workspaces"
    os.makedirs(path, exist_ok=True)
    yield path
    shutil.rmtree(path, ignore_errors=True)



