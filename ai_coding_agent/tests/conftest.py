"""Configuration for tests to initialize things like loggging."""

import logging
import os
import shutil
import tempfile
from collections.abc import AsyncGenerator, Generator
from dataclasses import dataclass
from pathlib import Path
from typing import TypeVar
from uuid import uuid4

import pytest
import pytest_asyncio

from ai_coding_agent.core.agents.dev_agent import DevAgent
from ai_coding_agent.core.logger import get_logger, silence_third_party_loggers
from ai_coding_agent.core.report_generator import generate_html_report
from ai_coding_agent.core.result import is_ok, on_error, unwrap
from ai_coding_agent.core.tools.result_types import TaskResult

T = TypeVar("T")
logger = get_logger(__name__)


@pytest.fixture(autouse=True)
def setup_test_logging(caplog):
    """Set up logging for all tests."""
    silence_third_party_loggers()
    caplog.set_level(logging.DEBUG)


@pytest.fixture
def workspace_base_path() -> Generator[str, None, None]:
    """Fixture to provide a temporary base path for workspaces."""
    base_path = tempfile.mkdtemp()
    try:
        yield base_path
    finally:
        shutil.rmtree(base_path, ignore_errors=True)


@dataclass
class TestInfo:
    """Test information for DevAgent tests."""

    dev_agent: DevAgent
    test_name: str


@pytest_asyncio.fixture
async def dev_agent(workspace: tuple[str, str], request) -> TestInfo:
    """Fixture to provide a DevAgent instance.

    This is the correct fixture for 90% of cases. Only tests that either don't involve the agent
    or tests that that test at a higher level (API/CLI) should not use this fixture.

    Args:
        workspace: Tuple of (workspace_id, workspace_path)
        request: Pytest request object

    Returns:
        A DevAgent instance configured with the workspace
    """
    _, workspace_path = workspace
    agent = DevAgent(workspace_path=Path(workspace_path))
    # We want to keep this figure low and only tests that need more iterations should override this
    agent.max_iterations = 8
    logger.info("Running test: %s", request.node.name)
    return TestInfo(agent, request.node.name)


async def go_and_generate_report(
    *,
    dev_agent: DevAgent,
    test_name: str,
    command: str,
    acceptance_criteria: str | None = None,
) -> TaskResult:
    """Execute agent command and generate report if correlation ID exists.

    Args:
        dev_agent: The DevAgent instance
        command: Command to execute
        acceptance_criteria: Acceptance criteria for the command
        test_name: The name of the test

    Returns:
        Result containing the agent response or error
    """
    result = await dev_agent.go(command, acceptance_criteria)
    if is_ok(result):
        correlation_id = unwrap(result).correlation_id
        if correlation_id:
            generate_html_report(
                f"{correlation_id}.json", f"{test_name}-{correlation_id}.html"
            )
    return result
