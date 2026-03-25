"""Test utilities and helpers."""

import json
from pathlib import Path
from typing import Any, Dict


class MockLLM:
    """Mock LLM client for testing."""

    def __init__(self, responses: Dict[str, Any]):
        """Initialize with predefined responses.

        Args:
            responses: Dictionary mapping prompts to responses
        """
        self.responses = responses
        self.calls = []

    def generate_text(self, system_prompt: str, user_prompt: str, **kwargs) -> str:
        """Mock text generation."""
        self.calls.append({"type": "text", "system": system_prompt, "user": user_prompt})

        # Find matching response
        for key, response in self.responses.items():
            if key in user_prompt:
                return response if isinstance(response, str) else json.dumps(response)

        return "Mock response"

    def generate_json(self, system_prompt: str, user_prompt: str, **kwargs) -> Dict:
        """Mock JSON generation."""
        self.calls.append({"type": "json", "system": system_prompt, "user": user_prompt})

        # Find matching response
        for key, response in self.responses.items():
            if key in user_prompt:
                return response if isinstance(response, dict) else json.loads(response)

        return {}


class MockSearch:
    """Mock search tool for testing."""

    def __init__(self, results: list):
        """Initialize with predefined results.

        Args:
            results: List of search results
        """
        self.results = results

    def search(self, query: str, num_results: int = 10) -> list:
        """Mock search."""
        return self.results[:num_results]


class TempDirectory:
    """Context manager for temporary directories."""

    def __init__(self, parent: Path = None):
        """Initialize temporary directory.

        Args:
            parent: Parent directory
        """
        import tempfile
        self.temp_dir = Path(tempfile.mkdtemp(dir=parent))

    def __enter__(self) -> Path:
        """Enter context."""
        return self.temp_dir

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit context and cleanup."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)


def load_test_data(name: str) -> Any:
    """Load test data from fixtures.

    Args:
        name: Test data name

    Returns:
        Test data
    """
    fixtures_dir = Path(__file__).parent / "fixtures"
    file_path = fixtures_dir / f"{name}.json"

    if file_path.exists():
        return json.loads(file_path.read_text())

    return None


def create_test_state(**overrides) -> Dict[str, Any]:
    """Create a test state with optional overrides.

    Args:
        **overrides: State overrides

    Returns:
        Test state
    """
    from src.state import create_initial_state

    state = create_initial_state("Test Topic")
    state.update(overrides)
    return state


def assert_valid_document(content: str, min_words: int = 1000) -> None:
    """Assert that content is a valid document.

    Args:
        content: Document content
        min_words: Minimum word count

    Raises:
        AssertionError: If validation fails
    """
    # Check word count
    words = len(content.split())
    assert words >= min_words, f"Document too short: {words} words"

    # Check for sections
    assert "#" in content, "Missing section headers"

    # Check for citations
    assert "[Source:" in content or len(content) > 5000, "Missing citations"

    # Check for placeholder text
    placeholders = ["placeholder", "TODO", "FIXME", "Lorem ipsum"]
    for placeholder in placeholders:
        assert placeholder.lower() not in content.lower(), f"Found placeholder: {placeholder}"


def measure_execution_time(func, *args, **kwargs) -> tuple[Any, float]:
    """Measure execution time of a function.

    Args:
        func: Function to measure
        *args: Function arguments
        **kwargs: Function keyword arguments

    Returns:
        Tuple of (result, elapsed_seconds)
    """
    import time

    start = time.time()
    result = func(*args, **kwargs)
    elapsed = time.time() - start

    return result, elapsed
