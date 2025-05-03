"""Functions used to create agents."""

import os
import platform
import sys
from typing import Any, Dict, Optional

import jinja2
import yaml
from langchain.agents import (
    AgentExecutor,
    create_openai_functions_agent,  # type: ignore
)
from langchain.prompts import (
    ChatPromptTemplate,
    HumanMessagePromptTemplate,
    MessagesPlaceholder,
)
from langchain_core.callbacks import BaseCallbackHandler
from langchain_core.messages import SystemMessage
from langchain_core.tools import BaseTool
from langchain_openai import ChatOpenAI

# Define paths for prompt templates
PROMPT_DIR = "config/prompts"
TASK_PROMPT_PATH = os.path.join(PROMPT_DIR, "task_message.yaml")
SYSTEM_PROMPT_PATH = os.path.join(PROMPT_DIR, "system_info.yaml")


def load_prompt_from_config(
    config_path: str, context_override: Optional[Dict[str, Any]] = None
) -> str:
    """Load prompt template from a YAML config file and render it with Jinja2.

    Args:
        config_path: Path to the YAML config file.
        context_override: Dictionary of context variables to override.

    Returns:
        The rendered prompt template.

    Raises:
        FileNotFoundError: If the config file doesn't exist.
    """
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Prompt file {config_path} does not exist")

    try:
        with open(config_path, "r") as file:
            config = yaml.safe_load(file)

        if not config or "template" not in config:
            raise ValueError(f"Invalid prompt config file: {config_path}")

        template_str = config.get("template", "")
        template = jinja2.Template(template_str)

        # Merge context from config with any overrides
        context = config.get("context", {})
        if context_override:
            context.update(context_override)

        rendered_template = template.render(**context)

        return rendered_template
    except Exception as e:
        raise RuntimeError(f"Error loading prompt config {config_path}: {e}")


def get_system_info_prompt() -> str:
    """Get the system info prompt with current system details.

    Returns:
        The rendered system info prompt.
    """
    system_context = {
        "os_system": platform.system(),
        "os_version": platform.version(),
        "os_release": platform.release(),
        "architecture": platform.machine(),
        "python_version": platform.python_version(),
        "platform": sys.platform,
    }

    return load_prompt_from_config(SYSTEM_PROMPT_PATH, system_context)


def get_prompt_template(
    task_config_path: str = TASK_PROMPT_PATH,
) -> ChatPromptTemplate:
    """Get the prompt template for the agent.

    Args:
        task_config_path: Path to the task prompt config file.

    Returns:
        The prompt template.
    """
    task_message = load_prompt_from_config(task_config_path)
    system_info = get_system_info_prompt()

    return ChatPromptTemplate.from_messages(
        [
            HumanMessagePromptTemplate.from_template(
                task_message,
            ),
            MessagesPlaceholder(variable_name="chat_history", optional=True),
            SystemMessage(content=system_info),
            MessagesPlaceholder(variable_name="agent_scratchpad"),
            MessagesPlaceholder(variable_name="notes"),
        ],
    )


def create_agent(
    llm: ChatOpenAI,
    prompt: ChatPromptTemplate,
    tools: list[BaseTool],
) -> Any:
    """Create the tools capable agent. Currently only OpenAI, but will be extended to other providers in the future.

    Args:
        llm: The language model to use.
        prompt: The prompt template.
        tools: The tools available to the agent.

    Returns:
        The OpenAI functions agent.
    """
    return create_openai_functions_agent(
        llm=llm,
        prompt=prompt,
        tools=tools,
    )


def create_agent_executor(
    agent: Any,
    tools: list[BaseTool],
    max_iterations: int,
    callbacks: list[BaseCallbackHandler],
) -> AgentExecutor:
    """Create the agent executor.

    Args:
        agent: The agent to execute.
        tools: The tools available to the agent.
        max_iterations: Maximum number of iterations.
        callbacks: Callback handlers.

    Returns:
        The agent executor.
    """
    return AgentExecutor(
        agent=agent,
        tools=tools,
        handle_parsing_errors=True,
        max_iterations=max_iterations,
        return_intermediate_steps=True,
        verbose=True,
        max_execution_time=300,  # 5 minutes max per attempt
        early_stopping_method="force",
        callbacks=callbacks,
    )
