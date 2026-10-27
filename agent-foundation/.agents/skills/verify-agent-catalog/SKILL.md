---
name: verify-agent-catalog
description: Verify this project's read-only Gradio Agent catalog through its real CLI and browser, including discovery, reload and configuration failures. Does not run models or evaluations.
---

Run from the project root. Read [the feature map](features/README.md) and the mapped journey. The product requirements and build workflow retain their existing approvals.

1. **Launch:** use `.venv-catalog/bin/python -B -m foundation.web --port 7863` in an owned terminal/session. This existing environment uses `requirements-catalog.lock`. Record the actual command/session identity and output. It listens on 127.0.0.1, sharing/analytics/monitoring are disabled. If binding is sandbox-denied, request the normal execution permission; if the port is occupied, stop without touching its owner. Do not launch a model or the stopped experiments.
2. **Doctor:** run `.venv-catalog/bin/python -B -m foundation.cli inspect knowledge_helper`. In the browser open `http://127.0.0.1:7863`; require the Agent 配置工作台 heading, knowledge_helper selection and the same source version/model declaration as the CLI. A URL or listening process alone is insufficient. Inspect returns 2 for config/source failure; 0 does not prove business/model readiness.
3. **Drive:** follow [catalog discovery and modification](features/catalog.md). Use available browser controls and visible labels; re-observe after actions. Do not substitute a callback/API/unit check for browser evidence.
4. **Evidence:** preserve actual commands, exits, input/source identities, visible states and screenshots under the current feature's durable evidence directory. Compare CLI and page versions, preserved assets and error meaning. The initial run lives in `features/observability_oss_audit/evidence/ticket1-20261025/`; create a distinct run directory for a new run rather than overwrite it.
5. **Cleanup:** stop only the server started in step1 using Ctrl-C in its recorded terminal/session; observe process completion. Remove only this run's owned temporary Agent, refresh and verify its old configuration is cleared. Preserve evidence and verify it still exists. For user handoff, a new explicitly recorded server may remain running after the verification instance is stopped.

Coverage is itemized in the feature map. Catalog evidence does not establish tool execution, Schema enforcement, model behavior, business quality, evaluation, MLflow or complete framework acceptance.
