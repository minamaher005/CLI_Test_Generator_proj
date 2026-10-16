"""TestGen - an agentic Python unittest generator.

An LLM agent writes tests with native tool calling (analyze the AST, write the
file, run pytest, measure coverage), observes every result, and repairs the
tests it authored until they pass - or until the iteration budget runs out.
"""
