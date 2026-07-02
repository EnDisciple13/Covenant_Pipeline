# Covenant Pipeline

Extract structured covenant data from credit agreement PDFs using a multi-stage pipeline: deterministic PDF chunking and routing, Gemini LLM extraction, relational compilation, integrity audit, and LLM-as-judge validation. An optional React/FastAPI viewer lets risk analysts verify extractions against source PDF pages.

**Full architecture and module documentation:** [PROJECT_DOCUMENTATION.md](PROJECT_DOCUMENTATION.md)

## Prerequisites

- **Python 3.10+**
- **Gemini API key** (required for `extract` and `validate` stages)
- **Node.js + npm** (optional, for the Covenant Viewer UI)

## Install

```bash
cd Covenant_Pipeline
pip install -e .

# Viewer support (FastAPI backend launcher)
pip install -e ".[viewer]"

# Frontend dependencies (first time only)
cd viewer/frontend && npm install
```

## Configure API Key

```bash
copy .env.example .env    # Windows
# cp .env.example .env    # macOS/Linux
```

Edit `.env` and set `GEMINI_API_KEY`. Get a key at https://aistudio.google.com/apikey

## Quick Start

```bash
# Full pipeline (writes artifacts to out/ by default)
covenant-pipeline run --pdf Credit_Agreement_Hallador.pdf

# Full pipeline + open viewer when done
covenant-pipeline run --pdf Credit_Agreement_Hallador.pdf --serve-ui

# Deterministic stages only (no API key needed)
covenant-pipeline run --pdf agreement.pdf --skip-llm
```

## CLI Commands

| Command | Description |
|---------|-------------|
| `covenant-pipeline run` | Run all stages in order |
| `covenant-pipeline chunk` | Phase 0: PDF → CSV chunks |
| `covenant-pipeline route` | Tier 1 routing → dispatch queue |
| `covenant-pipeline glossary` | Phase 2a: Article 1 definitions |
| `covenant-pipeline extract` | Phase 1: LLM extraction |
| `covenant-pipeline compile` | Phase 2b: relational compiler |
| `covenant-pipeline audit` | Phase 3a: integrity audit |
| `covenant-pipeline validate` | Phase 3b: LLM validation |
| `covenant-pipeline serve` | Launch viewer for existing output |

### Common flags

| Flag | Default | Description |
|------|---------|-------------|
| `--output-dir` | `out/` (repo root) | Directory for all pipeline artifacts |
| `--pdf` | `{output-dir}/Credit_Agreement_Hallador.pdf` | Source PDF (`run`, `chunk`, `serve`) |
| `--config` | `config/covenant_config.json` | Routing rules JSON |
| `--model` | `gemini-3.1-flash-lite` | Gemini model for extract/validate |
| `--rate-limit` | `2.0` | Seconds between LLM API calls |
| `--skip-llm` | off | Run chunk, route, glossary only (`run`) |
| `--adversarial` | off | Inject bad data during validation (testing) |
| `--serve-ui` | off | Launch viewer after pipeline (`run`) |
| `--no-browser` | off | Do not auto-open browser (`serve`) |

### Individual stages

```bash
covenant-pipeline chunk --pdf agreement.pdf
covenant-pipeline route
covenant-pipeline glossary
covenant-pipeline extract
covenant-pipeline compile
covenant-pipeline audit
covenant-pipeline validate

# Viewer only (requires prior full run)
covenant-pipeline serve --pdf agreement.pdf
```

## Pipeline Artifacts

All files are written to `out/` by default (override with `--output-dir`):

| File | Stage | Description |
|------|-------|-------------|
| `final_spatial_map.csv` | chunk | Section/page boundary map |
| `final_extracted_covenants.csv` | chunk | Master audit CSV (unscrubbed + clean text) |
| `final_extracted_covenants_phase1_payload.csv` | chunk | Slim CSV for routing, glossary, validation |
| `dispatch_queue_output.json` | route | LLM extraction envelopes |
| `resolved_definitions.json` | glossary | Article 1 definition graph |
| `phase1_extracted_nodes.json` | extract | Per-covenant structured LLM output + cost |
| `final_compiled_payload.json` | compile + audit | Merged payload with glossary + metadata |
| `final_compiled_payload_audited.json` | validate | Final payload with `Validation_Audit` per covenant |

## Programmatic API

```python
from covenant_pipeline.config import PipelinePaths
from covenant_pipeline.orchestrator import run_full_pipeline, run_stage

paths = PipelinePaths(pdf_path="agreement.pdf")
run_full_pipeline(paths)
# or: run_stage("extract", paths)
```

## Package Layout

```
covenant_pipeline/     # Core pipeline (CLI entry: covenant-pipeline)
config/                # covenant_config.json routing rules
out/                   # Default pipeline output directory (gitignored)
data/                  # Docker volume mount (PDF in, artifacts in data/out/)
viewer/                # FastAPI backend + React frontend
legacy/                # Prior monolith and old documentation (reference only)
```

## Docker (Phase 1)

Run the pipeline and viewer in isolated containers. Requires [Docker Desktop](https://www.docker.com/products/docker-desktop/).

**Full containerization reference:** [Docker_Documentation.md](Docker_Documentation.md)

### Setup

```bash
copy .env.docker.example .env.docker    # Windows
# cp .env.docker.example .env.docker    # macOS/Linux
```

Edit `.env.docker` and set `GEMINI_API_KEY` (required for full pipeline runs; not needed for `--skip-llm`).

Place your source PDF at `data/Credit_Agreement_Hallador.pdf` (or override paths in `docker-compose.yml`).

### Run the pipeline

```bash
# Deterministic stages only (no API key)
docker compose --profile pipeline run --rm pipeline run --skip-llm --pdf /app/data/Credit_Agreement_Hallador.pdf --output-dir /app/data/out

# Full pipeline (requires GEMINI_API_KEY in .env.docker)
docker compose --profile pipeline run --rm pipeline
```

Artifacts are written to `data/out/` on the host.

### Serve the viewer

```bash
docker compose up backend frontend
```

- Viewer: http://localhost:5173
- API: http://localhost:8000

The frontend Nginx container proxies `/api/*` to the backend service.
