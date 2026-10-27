"""Compose LangChain's standard agent loop with our reusable harness policies."""
from __future__ import annotations
from .config import AgentSpec
from .models import make_model
from .registry import load_tools


def build_agent(spec: AgentSpec, *, model_override=None):
    # Keep heavy imports here: `agentkit list/doctor` work without model packages.
    from langchain.agents import create_agent
    from langchain.agents.middleware import (
        HumanInTheLoopMiddleware,
        ModelCallLimitMiddleware,
        ToolCallLimitMiddleware,
        ToolRetryMiddleware,
    )
    from langgraph.checkpoint.memory import InMemorySaver

    tools = load_tools(spec)
    middleware = []
    # Approval middleware wraps the retries: one human decision per proposed action.
    if spec.approval_tools:
        middleware.append(HumanInTheLoopMiddleware(
            interrupt_on={name: {"allowed_decisions": ["approve", "reject"]}
                          for name in spec.approval_tools},
            interrupt_mode="batched",
        ))
    middleware.extend([
        ModelCallLimitMiddleware(run_limit=spec.max_model_calls, exit_behavior="end"),
        ToolCallLimitMiddleware(run_limit=spec.max_tool_calls),
    ])
    # Retry transient connectivity failures only. Never blindly retry writes.
    if spec.retry_tools and spec.retry_attempts:
        middleware.append(ToolRetryMiddleware(
            tools=list(spec.retry_tools), max_retries=spec.retry_attempts,
            retry_on=(ConnectionError, TimeoutError),
            on_failure="continue", initial_delay=0.2,
        ))
    return create_agent(
        model=model_override if model_override is not None else make_model(spec),
        tools=tools,
        system_prompt=spec.instructions,
        middleware=middleware,
        checkpointer=InMemorySaver(),  # Thread state only lives for this Python process.
        name=spec.name,
    )
