"""Configuration management for the research document generator.

Handles environment variables, API keys, and application settings.
"""

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional

from dotenv import load_dotenv

# Load environment variables from .env file
env_path = Path(__file__).parent.parent / ".env"
if env_path.exists():
    load_dotenv(env_path)
else:
    load_dotenv()  # Try default locations


@dataclass
class LLMConfig:
    """Configuration for Ollama client."""

    provider: str = "ollama"
    model: str = "llama3.1:8b"
    planner_model: Optional[str] = None
    researcher_model: Optional[str] = None
    writer_model: Optional[str] = None
    editor_model: Optional[str] = None
    base_url: str = "http://localhost:11434"
    api_key: Optional[str] = None
    temperature: float = 0.7
    max_tokens: int = 4096
    timeout: int = 300
    context_window: int = 32768

    def __post_init__(self) -> None:
        """Load from environment."""
        if provider_env := os.getenv("LLM_PROVIDER"):
            self.provider = provider_env
        if model_env := os.getenv("LLM_MODEL"):
            self.model = model_env
        
        self.planner_model = os.getenv("PLANNER_MODEL") or self.model
        self.researcher_model = os.getenv("RESEARCHER_MODEL") or self.model
        self.writer_model = os.getenv("WRITER_MODEL") or self.model
        self.editor_model = os.getenv("EDITOR_MODEL") or self.model
        
        if base_url_env := os.getenv("LLM_BASE_URL"):
            self.base_url = base_url_env


@dataclass
class SearchConfig:
    """Configuration for Wikipedia research."""

    provider: str = "wikipedia"
    max_results: int = 3
    timeout: int = 30

    def __post_init__(self) -> None:
        """Load from environment."""
        if provider_env := os.getenv("SEARCH_PROVIDER"):
            self.provider = provider_env
        if max_results_env := os.getenv("SEARCH_MAX_RESULTS"):
            self.max_results = int(max_results_env)


@dataclass
class OutputConfig:
    """Configuration for document output."""

    formats: List[str] = field(default_factory=lambda: ["markdown"])
    output_dir: Path = field(default_factory=lambda: Path("output"))
    include_toc: bool = True
    include_metadata: bool = True

    def __post_init__(self) -> None:
        """Ensure output directory exists."""
        self.output_dir = Path(self.output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)


@dataclass
class WorkflowConfig:
    """Configuration for the research workflow."""

    max_iterations: int = 2  # Max editor feedback loops
    enable_human_in_loop: bool = True  # Pause after planning
    target_word_count: int = 2500
    sections_count: int = 5  # Number of sections to generate
    words_per_section: int = 450  # Target words per section


def load_config_from_env():
    """Load configuration from environment variables."""
    return {
        "llm": LLMConfig(),
        "search": SearchConfig(),
        "output": OutputConfig(),
        "workflow": WorkflowConfig(),
    }


@dataclass
class AppConfig:
    """Main application configuration container.

    Provides centralized access to all configuration sections.
    """

    llm: LLMConfig = field(default_factory=LLMConfig)
    search: SearchConfig = field(default_factory=SearchConfig)
    output: OutputConfig = field(default_factory=OutputConfig)
    workflow: WorkflowConfig = field(default_factory=WorkflowConfig)
    debug: bool = False

    def __post_init__(self) -> None:
        """Load debug mode from environment."""
        self.debug = os.getenv("DEBUG", "false").lower() == "true"

    @classmethod
    def from_env(cls) -> "AppConfig":
        """Create configuration from environment variables."""
        return cls(
            llm=LLMConfig(),
            search=SearchConfig(),
            output=OutputConfig(),
            workflow=WorkflowConfig(),
        )

    def validate(self) -> List[str]:
        """Validate configuration."""
        errors = []
        import urllib.request
        try:
            urllib.request.urlopen(f"{self.llm.base_url}/api/tags", timeout=5)
        except:
            errors.append(f"Cannot connect to Ollama at {self.llm.base_url}")
        return errors


# Global configuration instance
_config: Optional[AppConfig] = None


def get_config() -> AppConfig:
    """Get or create global configuration instance.

    Returns:
        Application configuration
    """
    global _config
    if _config is None:
        _config = AppConfig.from_env()
    return _config


def set_config(config: AppConfig) -> None:
    """Set global configuration instance.

    Args:
        config: Configuration to use
    """
    global _config
    _config = config


def reset_config() -> None:
    """Reset global configuration to None."""
    global _config
    _config = None
