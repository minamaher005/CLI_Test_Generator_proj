# Microsoft_CLI_Test_Generator


A command-line tool that automatically generates Python **unittest** test files for any given Python function — powered by a specialized LLM.

## How It Works

### Why AST?

Python doesn't just read your code as plain text — internally, it parses source code into an **Abstract Syntax Tree (AST)** before execution. We leverage Python's built-in `ast` module to do the same: we parse the input `.py` file into its AST representation to validate its structure. This lets us programmatically verify that the file contains **only imports and exactly one function** before sending it to the LLM — no regex hacks, no fragile string matching.

### Why argparse?

Since this is a CLI tool meant to be run from the terminal, we use Python's `argparse` module to define and parse command-line arguments. This gives us proper argument validation, help messages, and error handling out of the box.

### Why unittest?

The project requires generating a `.py` test file. We chose Python's built-in `unittest` library as the test framework because:

- It's part of the standard library — zero extra dependencies for the generated tests
- It provides a structured, class-based approach to organizing test cases
- It's widely understood and universally supported

### Why qwen3-coder-next?

We use **qwen3-coder-next** via [Ollama](https://ollama.com) — a specialized code-generation LLM optimized for programming tasks. The model is called with `temperature=0` to ensure deterministic, precise output that sticks strictly to the system prompt and produces only the test code — no explanations, no markdown, no commentary.

## Project Structure

```
testgen/
├── cli.py              # Entry point — parses CLI arguments, orchestrates the pipeline
├── filecheck.py        # AST-based validator — ensures file has imports + exactly one function
├── prompt_builder.py   # Reads the source file, builds the LLM prompt with examples
├── llm_client.py       # Ollama client — sends prompt to qwen3-coder-next, writes output
├── requirements.txt    # Python dependencies
├── .env                # API keys (not committed)
└── README.md           # This file
```

### Pipeline Flow

```
cli.py  →  filecheck.py  →  prompt_builder.py  →  llm_client.py  →  {filename}_test.py
 (args)      (AST validate)    (build prompt)      (call LLM)         (output)
```

## Setup

### 1. Clone the repo

```bash
git clone https://github.com/minamaher005/Microsoft_CLI_Test_Generator.git
cd Microsoft_CLI_Test_Generator
```

### 2. Install dependencies

```bash
pip install ollama python-dotenv
```

### 3. Configure environment

Create a `.env` file in the project root:

```env
OLLAMA_API_KEY=your_ollama_api_key_here
```

## Usage

```bash
python cli.py <path_to_python_file.py>
```

### Example

Given a file `math_utils.py`:

```python
import math

def circle_area(radius: float) -> float:
    if radius < 0:
        raise ValueError("Radius cannot be negative")
    return math.pi * radius ** 2
```

Run:

```bash
python cli.py math_utils.py
```

Output: a `math_utils.py_test.py` file containing comprehensive unittest test cases covering all edge cases.

### Rules for Input Files

The input `.py` file must contain:

- **Only imports** (`import` / `from ... import`)
- **Exactly one function** (`def`)
- No classes, no top-level statements, no global variables

If the file doesn't meet these criteria, the tool will reject it with a clear message.

## Model Details

| Parameter   | Value               |
| ----------- | ------------------- |
| Provider    | Ollama              |
| Model       | qwen3-coder-next    |
| Temperature | 0                   |
| Task        | unittest generation |
