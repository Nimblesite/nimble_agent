"""CLI command interface for Nimble Agent.

It handles workspace management and task execution through Click.
"""

import asyncio
import os
from pathlib import Path
from typing import Self

import click

from ai_coding_agent.core.agents.dev_agent import DevAgent
from ai_coding_agent.core.constants import (
    DEFAULT_GPT_MODEL,
    DEFAULT_MAXITERATIONS,
    DEFAULT_TEMPERATURE,
)
from ai_coding_agent.core.logger import get_logger
from ai_coding_agent.core.report_generator import generate_html_report
from ai_coding_agent.core.result import Err, Ok, Result, either

logger = get_logger(__name__)


class NimbleAgentCLI:
    """Main CLI handler for Nimble Agent.

    Manages workspaces and provides high-level interface for running AI-powered coding tasks.
    """

    def __init__(self: Self) -> None:
        """Initialize the CLI handler.

        Args:
            workspace_manager: Optional workspace manager instance. If not provided,
                             a new one will be created with default settings.
        """
        self.logger = get_logger(__name__)


@click.group()
def cli() -> None:
    """Nimble Agent - Your reliable partner for tackling tech debt.

    Set it. Forget it. Review it.
    A practical tool that works alongside you to pay down tech debt one step at a time.
    """


@cli.command()
@click.argument("task")
@click.option(
    "--workspace-path",
    type=click.Path(exists=True, file_okay=False, dir_okay=True),
    help="Path to workspace directory. Defaults to current directory.",
)
@click.option(
    "--acceptance-criteria",
    help="Optional criteria that must be met for the task to be considered complete.",
)
@click.option(
    "--max-iterations",
    type=int,
    default=DEFAULT_MAXITERATIONS,
    help=f"Maximum iterations to attempt task. Default: {DEFAULT_MAXITERATIONS}",
)
@click.option(
    "--model",
    default=DEFAULT_GPT_MODEL,
    help=f"LLM model to use. Default: {DEFAULT_GPT_MODEL}",
)
@click.option(
    "--temperature",
    type=float,
    default=DEFAULT_TEMPERATURE,
    help=f"Model temperature (0.0-1.0). Default: {DEFAULT_TEMPERATURE}",
)
@click.option(
    "--api-key",
    envvar="OPENAI_API_KEY",
    help="OpenAI API key. Can also be set via OPENAI_API_KEY environment variable.",
)
def run(
    task: str,
    workspace_path: Path | None = None,
    acceptance_criteria: str | None = None,
    max_iterations: int = DEFAULT_MAXITERATIONS,
    model: str = DEFAULT_GPT_MODEL,
    temperature: float = DEFAULT_TEMPERATURE,
    api_key: str | None = None,
) -> None:
    """Run an AI-powered coding task in your workspace.

    A dependable assistant that tackles tedious, time-consuming work so you can focus on innovation.
    Each task operates in an isolated workspace to ensure safe execution.

    Authentication:
        An OpenAI API key is required. You can provide it in one of two ways:
        1. Environment variable: export OPENAI_API_KEY='your-api-key'
        2. CLI argument: --api-key='your-api-key'

    Examples:
        # Using environment variable
        $ export OPENAI_API_KEY='your-api-key'
        $ nimbleagent run "Update all dependencies to their latest compatible versions"

        # Using CLI argument
        $ nimbleagent run --api-key='your-api-key' "Apply consistent error handling patterns"

        # Dependency Management
        $ nimbleagent run "Update all dependencies to their latest compatible versions"

        # Code Quality
        $ nimbleagent run "Apply consistent error handling patterns across the codebase"

        # Technical Debt
        $ nimbleagent run "Extract duplicated code into reusable functions"

        # Testing
        $ nimbleagent run "Add unit tests for uncovered code paths"
    """
    try:
        if api_key:
            os.environ["OPENAI_API_KEY"] = api_key

        loop = asyncio.get_event_loop()
        if loop.is_running():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        if workspace_path is None:
            workspace_path_path = Path.cwd()
        else:
            path = Path(workspace_path)
            if not path.is_absolute():
                path = Path.cwd() / path

            if not path.exists():
                raise click.ClickException(f"Workspace path does not exist: {path}")

            if not path.is_dir():
                raise click.ClickException(f"Workspace path is not a directory: {path}")

            workspace_path_path = path

        result = loop.run_until_complete(
            run_task(
                workspace_path=workspace_path_path,
                task=task,
                acceptance_criteria=acceptance_criteria,
                max_iterations=max_iterations,
                model=model,
                temperature=temperature,
            ),
        )
        click.echo(result)
    except click.ClickException:
        raise
    except Exception as e:
        raise click.ClickException(str(e)) from e


CLIRunResult = Result[str, str]


async def run_task(
    task: str,
    workspace_path: Path,
    acceptance_criteria: str | None = None,
    max_iterations: int = DEFAULT_MAXITERATIONS,
    model: str = DEFAULT_GPT_MODEL,
    temperature: float = DEFAULT_TEMPERATURE,
) -> CLIRunResult:
    """Run a task in the specified workspace.

    Args:
        workspace_path: The path of the workspace to run the task in.
        task: The task to run.
        acceptance_criteria: acceptance criteria for the task that determines whether or not the task is complete.
        max_iterations: Maximum number of iterations to run.
        model: The model to use.
        temperature: The temperature to use.

    Returns:
        The result of the task.

    Raises:
        click.ClickException: If the workspace is not found or the task fails.
    """
    try:
        agent = DevAgent(
            workspace_path=workspace_path,
            model=model,
            temperature=temperature,
            max_iterations=max_iterations,
        )
        result = await agent.go(
            task=task,
            acceptance_criteria=acceptance_criteria,
        )

        task_output = either(result)
        correlation_id = task_output.correlation_id

        generate_html_report(f"{correlation_id}.json", f"{correlation_id}.html")

        match result:
            case Ok(task_output):
                logger.info(f"Task completed: {task_output.output_message}")
                return Ok(task_output.output_message)

            case Err(task_output):
                logger.error(f"Task failed: {task_output.output_message}")
                return Err(task_output.output_message)

    except Exception as e:
        logger.exception("Task failed")
        return Err(str(e))
