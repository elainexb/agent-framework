"""Public interface: inspect, scaffold, run, chat, offline demo, unit/live eval."""
from __future__ import annotations
import argparse
from importlib.util import find_spec
import json
from pathlib import Path
import sys
import uuid

from dotenv import load_dotenv
from .config import PROJECT_ROOT, list_agents, load_spec
from .scaffold import scaffold


def _doctor(name: str | None):
    for module in ["yaml", "dotenv", "langchain", "langgraph", "langchain_ollama"]:
        print(f"{module:20} {'OK' if find_spec(module) else 'MISSING'}")
    if name:
        spec = load_spec(name)
        print(f"agent: {spec.name} / provider: {spec.provider} / model: {spec.model}")
        print(f"tools ({len(spec.tools)}): {', '.join(spec.tools)}")
        print(f"approval tools: {list(spec.approval_tools)}")
        if spec.provider == "openai" and not find_spec("langchain_openai"):
            print("Missing optional package: pip install -e '.[openai]'")
    print("Note: dependency checks do NOT test a live LLM endpoint.")


def _offline_demo(name: str, question: str):
    print("[Offline deterministic demo: no LLM, no Agent Loop; only business services]")
    if name == "support_insights":
        from agents.support_insights.services import CSV_PATH, seed_demo_data, ticket_stats, ticket_examples
        if not CSV_PATH.exists():
            seed_demo_data()
        stats = ticket_stats(7)
        print("get_ticket_stats(7) ->", json.dumps(stats, ensure_ascii=False, indent=2))
        if stats["top_category"]:
            examples = ticket_examples(stats["top_category"], 7)
            print("get_ticket_examples(...) ->", json.dumps(examples, ensure_ascii=False, indent=2))
        print("No local Jira draft created; the real Agent can propose one for approval.")
    elif name == "knowledge_helper":
        from agents.knowledge_helper.services import search
        print("search_knowledge(...) ->", json.dumps(search(question), ensure_ascii=False, indent=2))
    else:
        print("No offline demo exists for this new agent. Add a demo to _offline_demo if useful.")


def _real_run(name: str, message: str | None, thread_id: str | None, trace: bool, chat: bool):
    from .builder import build_agent
    from .runner import run_turn
    spec = load_spec(name)
    graph = build_agent(spec)
    tid = thread_id or uuid.uuid4().hex
    print(f"Agent: {name} | session: {tid} | memory: in-process only")
    if chat:
        print("Enter /exit to quit; /trace to toggle tool-name tracing.")
        while True:
            try:
                question = input("\nYou> ").strip()
            except (EOFError, KeyboardInterrupt):
                print("\nGoodbye.")
                return
            if question in {"/exit", "/quit"}:
                return
            if question == "/trace":
                trace = not trace
                print("trace:", trace)
                continue
            if not question:
                continue
            print("\nAgent>", run_turn(graph, question, thread_id=tid, trace=trace))
    else:
        if not message:
            raise ValueError("run requires --message")
        print("\nAgent>", run_turn(graph, message, thread_id=tid, trace=trace))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="agentkit", description="Reusable modular Agent starter kit")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("list", help="List available agents")
    p_doctor = sub.add_parser("doctor", help="Check local Python dependencies and an agent spec")
    p_doctor.add_argument("agent", nargs="?")
    p_inspect = sub.add_parser("inspect", help="Inspect config/source status without importing tools or connecting models")
    p_inspect.add_argument("agent")
    p_scaffold = sub.add_parser("scaffold", help="Generate a new agent package")
    p_scaffold.add_argument("name")
    p_seed = sub.add_parser("seed", help="Create synthetic support ticket data")
    p_seed.add_argument("agent", choices=["support_insights"])
    p_seed.add_argument("--force", action="store_true", help="Explicitly overwrite example data")
    p_demo = sub.add_parser("demo", help="Offline deterministic business-logic demonstration")
    p_demo.add_argument("agent")
    p_demo.add_argument("--question", default="What is P0 escalation severity?")
    for cmd in ("run", "chat"):
        p = sub.add_parser(cmd, help="Run a real LLM-backed agent (requires model)")
        p.add_argument("agent")
        p.add_argument("--thread", help="Session ID (in-memory within current process)")
        p.add_argument("--trace", action="store_true", help="Print tool names, not private payloads")
        if cmd == "run":
            p.add_argument("--message", required=True)
    p_eval = sub.add_parser("eval", help="Run live LLM eval; NEVER auto-approve writes")
    p_eval.add_argument("agent")
    args = parser.parse_args(argv)
    load_dotenv(PROJECT_ROOT / ".env")
    try:
        if args.command == "list":
            for name in list_agents():
                spec = load_spec(name)
                print(f"{name:22} {spec.description}")
        elif args.command == "doctor":
            _doctor(args.agent)
        elif args.command == "inspect":
            from .catalog import inspect_agent
            report = inspect_agent(args.agent)
            print(json.dumps(report, ensure_ascii=False, indent=2))
            return 2 if any(report[key]["status"] == "FAIL" for key in ("configuration", "tools")) else 0
        elif args.command == "scaffold":
            print("Created:", scaffold(args.name))
            print("Edit: agent.yaml, instructions.md, services.py, tools.py, eval_cases.json")
        elif args.command == "seed":
            from agents.support_insights.services import seed_demo_data
            print("Data:", seed_demo_data(force=args.force))
        elif args.command == "demo":
            load_spec(args.agent)
            _offline_demo(args.agent, args.question)
        elif args.command in {"run", "chat"}:
            _real_run(args.agent, getattr(args, "message", None), args.thread, args.trace, args.command == "chat")
        elif args.command == "eval":
            from .evaluation import live_evaluate
            results = live_evaluate(load_spec(args.agent))
            print(json.dumps(results, ensure_ascii=False, indent=2))
            return 0 if all(r["passed"] for r in results) else 1
        return 0
    except (ValueError, FileNotFoundError, FileExistsError, RuntimeError, ImportError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
