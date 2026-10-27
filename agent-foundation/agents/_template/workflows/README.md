# Optional deterministic workflows

For simple Agents, prefer a Tool implemented by `services.py`. If tasks require branching, parallel validation, resumable long-running work or deterministic control flow, add an explicit workflow using LangGraph StateGraph here, test it separately, and extend the builder to use it. This is an extension point, not an active automatic plugin.
