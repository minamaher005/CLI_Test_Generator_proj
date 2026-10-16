# TestGen — an Agentic Test Generator for Python

A command-line tool where an **LLM agent** generates Python `unittest` files for you —
and it doesn't just write them and hope. The agent **uses tools natively**: it parses
your file's AST, writes the test module, *runs it with pytest*, reads the tracebacks,
measures line coverage, and **repairs its own tests until they pass**.

```
        ┌────────────────────────────────────────────────┐
        ▼                                                │
  ┌──────────────┐   ┌────────────┐   ┌───────────┐   ┌──┴────────────┐
  │  analyze_ast │──▶│ write_test │──▶│ run_tests │──▶│  get_coverage │
  │ (AST inspect)│   │ (sandboxed)│   │ (pytest)  │   │ (coverage.py) │
  └──────────────┘   └────────────┘   └───────────┘   └───────────────┘
```

*(Every arrow is a real tool call the model chose to make — not a hardcoded pipeline.)*

## What makes it agentic

| The old way (v1) | TestGen (v2) |
| --- | --- |
| One-shot prompt → file blindly written | Agent loop with **native tool calling** |
| Generated tests never executed | Tests are **actually run**; failures/tracebacks are fed back |
| No verification | **Line coverage** measured and reported |
| Hardcoded model & logs | Config-driven (`.env` + CLI flags), multi-provider |
| No tests for the tool itself | 15 pytest tests + ruff-clean + CI |

The agent decides each step and observes each result. If `pytest` fails, the model reads
the exact traceback and iterates (bounded by `--max-iterations`, default 5) until the
tests pass or the budget is spent.

## Tools exposed to the agent

| Tool | Behavior |
| --- | --- |
| `analyze_ast` | AST-parses the target file → functions, params, type hints, defaults, raised exceptions |
| `write_test` | Strips markdown fences, **syntax-validates**, writes only inside the `.testgen` sandbox |
| `run_tests` | Runs `pytest`, returns passed/failed/error counts + output tail with tracebacks |
| `get_coverage` | Runs coverage.py → line coverage % + exact uncovered line numbers |

## Architecture

```
src/testgen/
├── cli.py            # thin orchestrator: flags, validation, wiring
├── config.py         # env-driven configuration
├── agent/
│   ├── core.py       # the observe → think → act loop
│   ├── state.py      # conversation history + tool trace
│   └── prompts.py    # system prompt (agent role + tool policy)
├── tools/            # the agent's hands: base Tool/ToolRegistry + 4 tools
├── llm/              # OllamaProvider (tool calling) + MockProvider (offline)
├── validation/       # input gate: readable .py, parses, has functions
└── reporting/        # JSON report + rich console summary
```

## Setup

```bash
cd cli-testgen
python -m venv .venv
.venv\Scripts\python -m pip install -e ".[dev]"    # (or pip install -e ".[dev]")

cp .env.example .env    # then add your OLLAMA_API_KEY
```

## Usage

```bash
# With your Ollama API key (real LLM agent):
testgen <file.py>

# Fully offline, deterministic demo (no API key needed):
testgen <file.py> --provider mock
```

Example:

```bash
$ testgen tests/fixtures/add.py
 ──────────────────────────────────────────────────────
 → tool: analyze_ast          [iter 1]
 → tool: write_test           [iter 2]
 → tool: run_tests            [iter 3]
 → tool: get_coverage         [iter 4]
 ──────────────────────────────────────────────────────
 SUCCESS — Tests passed=5 failed=0 errors=0
 Coverage 100.0% (threshold: 80%)
 ──────────────────────────────────────────────────────
```

### Flags

| Flag | Default | Meaning |
| --- | --- | --- |
| `--provider` | `ollama` | `ollama` (LLM) or `mock` (offline scripted agent) |
| `--model` | `gemma4:31b-cloud` | any Ollama model |
| `--max-iterations` | `5` | agent loop budget |
| `--coverage-threshold` | `80` | coverage % target |
| `--no-coverage` | off | skip the coverage tool |
| `--outdir` | `.testgen` | sandbox directory for outputs |
| `--verbose / -v` | off | show full tool payloads |

Artifacts land in `.testgen/`: the generated `*_test.py`, `coverage.json`, and
`report.json`.

## Development

```bash
.venv\Scripts\pytest tests        # run the test suite (no network needed)
.venv\Scripts\ruff check .        # lint
```

## Design notes

- **Reasoning with AST, not regex** — both the input gate and `analyze_ast` use Python's
  `ast` module to programmatically understand code structure.
- **Strict sandboxing** — `write_test` baseline-name-checks the filename and only writes
  into `.testgen/`; the source file is never modified.
- **Bounded autonomy** — the loop has a hard iteration budget; exhausted budget produces
  a partial report rather than infinite drift.
- **Deterministic reproduction** — the mock provider runs the *same tool loop* with no
  network needed, making demos and CI reliable.
- **Observability** — every agent decision, tool call, and payload is traceable
  (`--verbose`); every run produces a machine-readable `report.json`.
