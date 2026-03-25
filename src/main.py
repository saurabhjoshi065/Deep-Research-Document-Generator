"""CLI entry point for the Deep Research Document Generator."""

import argparse
import logging
import sys
from pathlib import Path
from src.graph import create_workflow
from src.state import create_initial_state

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)

def create_parser() -> argparse.ArgumentParser:
    """Create argument parser."""
    parser = argparse.ArgumentParser(
        prog="deep-research",
        description="Generate high-quality research documents using AI",
    )
    parser.add_argument("topic", help="Research topic to investigate")
    parser.add_argument("--sections", type=int, default=5, help="Number of sections (3-10)")
    parser.add_argument("--output-dir", type=str, default="output", help="Output directory")
    parser.add_argument("--max-iterations", type=int, default=2, help="Max revision iterations")
    parser.add_argument("--verbose", "-v", action="store_true", help="Enable verbose logging")
    return parser

def validate_inputs(args: argparse.Namespace) -> bool:
    """Validate arguments."""
    if not args.topic or len(args.topic.strip()) < 3:
        print("Error: Topic too short", file=sys.stderr); return False
    if args.sections < 2 or args.sections > 10:
        print("Error: Sections must be 2-10", file=sys.stderr); return False
    return True

def run_workflow(topic: str, args: argparse.Namespace) -> dict:
    """Run the research workflow."""
    logger.info(f"Starting research: {topic}")
    state = create_initial_state(topic=topic)
    state["max_iterations"] = args.max_iterations
    
    Path(args.output_dir).mkdir(parents=True, exist_ok=True)
    workflow = create_workflow()

    try:
        final_state = workflow.invoke(state)
        if final_state.get("current_step") == "error":
            raise RuntimeError(f"Workflow failed: {', '.join(final_state.get('errors', []))}")
        return final_state
    except Exception as e:
        logger.error(f"Execution failed: {e}"); raise

def print_results(state: dict) -> None:
    """Print results summary."""
    print("\n" + "=" * 60 + "\nRESEARCH COMPLETE\n" + "=" * 60)
    print(f"\nTopic: {state.get('topic')}\nStatus: {state.get('current_step')}")

    if state.get("drafts"):
        from src.state import get_total_word_count
        print(f"Total Words: {get_total_word_count(state)}")
        print(f"Sections: {len(state['drafts'])}")

    if state.get("final_document"):
        print("\nDocument generated successfully in 'output/' folder.")
    print("\n" + "=" * 60)

def main(args: list[str] | None = None) -> int:
    """Main entry point."""
    parser = create_parser()
    parsed_args = parser.parse_args(args)
    if parsed_args.verbose: logging.getLogger().setLevel(logging.DEBUG)
    if not validate_inputs(parsed_args): return 1

    try:
        final_state = run_workflow(parsed_args.topic, parsed_args)
        print_results(final_state)
        return 0
    except KeyboardInterrupt:
        print("\nCancelled by user", file=sys.stderr); return 130
    except Exception as e:
        print(f"\nError: {e}", file=sys.stderr); return 1

if __name__ == "__main__":
    sys.exit(main())
