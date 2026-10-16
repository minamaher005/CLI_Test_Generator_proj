from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


@dataclass
class Config:
    """Central configuration. Environment-provided defaults, overridable via CLI flags."""

    provider: str = "ollama"
    model: str = "gemma4:31b-cloud"
    temperature: float = 0.0
    max_iterations: int = 5
    coverage_threshold: float = 80.0
    use_coverage: bool = True
    output_dir: Path = Path(".testgen")
    ollama_host: str = "https://ollama.com"
    verbose: bool = False

    @classmethod
    def from_env(cls) -> Config:
        load_dotenv()
        return cls(
            provider=os.environ.get("TESTGEN_PROVIDER", "ollama"),
            model=os.environ.get("TESTGEN_MODEL", "gemma4:31b-cloud"),
            temperature=float(os.environ.get("TESTGEN_TEMPERATURE", "0")),
            max_iterations=int(os.environ.get("TESTGEN_MAX_ITERATIONS", "5")),
            coverage_threshold=float(os.environ.get("TESTGEN_COVERAGE_THRESHOLD", "80")),
            ollama_host=os.environ.get("OLLAMA_HOST", "https://ollama.com"),
        )
