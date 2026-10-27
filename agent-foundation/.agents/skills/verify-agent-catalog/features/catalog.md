# Catalog discovery and modification

Users can find the Agent Codex created and see the configuration that is currently on disk.

## Sub-features

- C1: Existing Agents appear with source version and declared model; model validation remains UNKNOWN.
- C2: A newly scaffolded Agent appears after reload and is blocked as an unfinished template. New creation refuses overwrite.
- C3: Modifying instructions then reloading changes the source version while unrelated assets retain their bytes.
- C4: Unintegrated configuration such as `memory` produces a clear FAIL rather than apparent support. Removing the selected temporary Agent clears its stale report.

## How to get to it (user POV)

Ask Codex to use build-agent for a new or existing Agent. Open the shared local page, choose its name, then use “重新载入列表与配置” after changes.

## Driving it with the local CLI and browser

Preconditions: the approved catalog environment exists; port7863 is free; `agents/catalog_probe` is absent; work is authorized for temporary technical fixtures. Reuse prior fixture ownership only from this run, never assume a pre-existing directory is disposable.

Launch and doctor via the parent Skill. For C1 compare `.venv-catalog/bin/python -B -m foundation.cli inspect knowledge_helper` with the page version. For C2 run `.venv-catalog/bin/python -B -m foundation.cli scaffold catalog_probe`; repeat and expect refusal, preserving the first directory. Click reload and choose catalog_probe: expect unfinished-template FAIL and model UNKNOWN.

For a technical configuration pilot reuse the inspected knowledge_helper config/instructions/tools/services/cases/handbook, adjusting only its name to catalog_probe; this is fixture preparation, not evidence of business value. Snapshot the resulting assets. Inspect by CLI, click reload and compare versions. For C3 change only the owned fixture's instructions, inspect and reload; expect a new matching version and unchanged other assets. For C4 retain a copy of the owned YAML, append `memory: {enabled: true}`, inspect and reload; expect configuration FAIL identifying memory. Restore the YAML, remove only this run's temporary Agent, reload and expect the stale selection/report cleared.

Save CLI reports, before/after identities, visible states and screenshots in this run's durable evidence folder. Stop the owned verification server and confirm completion; confirm retained evidence survives. A subsequent handoff server has a separate identity.

## Gotchas

The source version covers config, own instructions, tools.py, services.py and shared base instructions. It excludes weights, data, other imported modules and environment. Tool checks only parse source and resolve declared local function names; imports, decorators, Schema and execution remain unverified. Invalid config may have no source version. The page is read-only and does not persist a registry or support model/score operations. Reloading the browser reconstructs the catalog from disk.
