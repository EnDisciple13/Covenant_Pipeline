# Covenant Pipeline — agent entry point

Credit-agreement extraction pipeline. Registry id: `covenant_pipeline`.

This repository is proof space: implementation and as-built truth live here. Strategy and roadmap truth live canonically in the sibling Notes repository and are committed here as generated mirrors under `docs/platform-engineering/`.

## Read order

1. `PROJECT_DOCUMENTATION.md` — application documentation
2. `Docker_Documentation.md` — implementation and as-built documentation
3. `docs/platform-engineering/` — committed strategy mirrors available to local and online agents

When the sibling Notes repository is available locally, also read `../Notes/registry.yaml` and `../Notes/AGENTS.md` before cross-repo planning.

## Critical rules

- Never edit files carrying a `MIRROR:` banner under `docs/platform-engineering/`. Edit the canonical file in `../Notes/projects/covenant/platform-engineering/`, then run the Notes mirror sync.
- Roadmap and planning status is canonical in Notes; as-built truth is canonical in `Docker_Documentation.md` and the implementation.
- In Codex Online, the sibling Notes repository is not assumed to exist. Use committed strategy mirrors as read-only context and record any proposed canonical Notes change as a handoff rather than editing a mirror.
- Full HQ workflow skills live in the Notes repository and are available when Notes is open alongside this repo. An isolated online task should execute from committed project context or emit a handoff when it needs Notes-only machinery.
- Preserve unrelated user changes and verify implementation changes proportionally to risk.
