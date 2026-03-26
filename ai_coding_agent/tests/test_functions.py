"""Shared test functions used across test files."""

import shutil
import uuid
from collections.abc import Callable, Coroutine
from pathlib import Path
from tempfile import gettempdir
from typing import Any, TypeVar

from ai_coding_agent.core.logger import get_logger
from ai_coding_agent.core.result import Err, Ok, is_ok
from ai_coding_agent.core.tools.file_functions import write_file
from ai_coding_agent.core.tools.result_types import (
    DirectoryStateData,
    DirectoryStateResult,
)

logger = get_logger(__name__)
T = TypeVar("T")


async def create_test_file(filepath: Path, content: str) -> None:
    """Create a test file with the given content.

    Args:
        filepath: The absolute path to the file to create. Must be absolute.
        content: The content to write to the file

    Raises:
        ValueError: If filepath is not absolute
    """
    if not filepath.is_absolute():
        raise ValueError("filepath must be absolute")

    result = await write_file(filepath, content)
    assert is_ok(result)


async def runtest(test_function: Callable[[str], Coroutine[Any, Any, T]]) -> T:
    """Don't use this!!

    Creates a workspace, runs the test function, and deletes the workspace afterwards.

    Args:
        test_function: Async function that takes workspace path and performs test operations

    Returns:
        The return value from the test function

    Raises:
        ValueError: If workspace creation fails
    """
    workspace_base_path = Path(gettempdir()) / "ai_coding_agent_test_workspaces"

    if not workspace_base_path.exists():
        workspace_base_path.mkdir(parents=True, exist_ok=True)

    # Create unique workspace directory
    workspace_id = str(uuid.uuid4())
    workspace_path = workspace_base_path / workspace_id

    try:
        # Create the workspace directory
        workspace_path.mkdir(parents=True, exist_ok=True)

        # Run the test function with the workspace path
        return await test_function(str(workspace_path))
    finally:
        # Clean up workspace directory
        if workspace_path.exists():
            try:
                shutil.rmtree(workspace_path)
            except Exception:
                logger.exception(f"Error cleaning up workspace {workspace_path}")


# TODO: remove this. We shouldn't use this, even in tests. Usesless function.


async def get_directory(
    workspace_path: str | Path,
    current_dir: str = "",
) -> DirectoryStateResult:
    """Don't use this. Bad function.

    Get the current working directory.

    Args:
        workspace_path: Base workspace directory path
        current_dir: Current directory relative to workspace root

    Returns:
        DirectoryStateResult with current directory information
    """
    try:
        workspace_path = Path(workspace_path)
        if not workspace_path.exists():
            return Err("Error: Workspace path does not exist")
        if not workspace_path.is_dir():
            return Err("Error: Workspace path is not a directory")
        return Ok(DirectoryStateData(directory=current_dir))
    except Exception as e:
        return Err(f"Error getting directory: {e}")
