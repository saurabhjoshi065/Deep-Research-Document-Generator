"""Workflow nodes for LangGraph."""

import logging
from typing import Any, Dict, List, Optional
from src.agents import EditorAgent, PlannerAgent, ResearchAgent, WriterAgent
from src.publishers import DocumentCompiler
from src.state import add_error, get_total_word_count, update_state

logger = logging.getLogger(__name__)

def planning_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """Planning node: Generate outline."""
    try:
        logger.info("Starting planning node")
        from src.config import get_config
        from src.llm.client import get_llm_client
        config = get_config()
        llm = get_llm_client(model_override=config.llm.planner_model)
        planner = PlannerAgent(llm_client=llm)

        # Respect section count from state if provided by UI
        target_sections = state.get("sections_count", config.workflow.sections_count)
        outline = planner.generate_outline(state["topic"], expected_sections=target_sections)
        return update_state(state, outline=[s.to_dict() for s in outline.sections], current_step="researching")
    except Exception as e:
        logger.error(f"Planning failed: {e}")
        return add_error(state, f"Planning failed: {e}")

def research_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """Research node: Gather data."""
    try:
        logger.info("Starting research node")
        from src.state import SectionOutline
        sections = [SectionOutline.from_dict(s) for s in state.get("outline", [])]
        if not sections: raise ValueError("No outline sections")

        from src.config import get_config
        from src.llm.client import get_llm_client
        config = get_config()
        llm = get_llm_client(model_override=config.llm.researcher_model)
        researcher = ResearchAgent(llm_client=llm)

        results = {s.title: [r.to_dict() for r in researcher.research_section(state["topic"], s).to_state_results()] for s in sections}
        return update_state(state, research=results, current_step="researching")
    except Exception as e:
        logger.error(f"Research failed: {e}")
        return add_error(state, f"Research failed: {e}")

def writing_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """Writing node: Draft sections."""
    try:
        logger.info("Starting writing node")
        from src.state import SectionOutline, SearchResult
        sections = [SectionOutline.from_dict(s) for s in state.get("outline", [])]
        research = {t: [SearchResult.from_dict(r) for r in res] for t, res in state.get("research", {}).items()}

        from src.config import get_config
        from src.llm.client import get_llm_client
        config = get_config()
        llm = get_llm_client(model_override=config.llm.writer_model)
        writer = WriterAgent(llm_client=llm)

        drafts = state.get("drafts", {})
        for s in sections:
            if s.title not in drafts:
                logger.info(f"Writing: {s.title}")
                drafts[s.title] = writer.write_section(state["topic"], s, research.get(s.title, [])).to_dict()

        return update_state(state, drafts=drafts, current_step="editing")
    except Exception as e:
        logger.error(f"Writing failed: {e}")
        return add_error(state, f"Writing failed: {e}")

def editing_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """Editing node: Review sections (optimized)."""
    try:
        logger.info("Starting editing node")
        from src.state import SectionOutline, SearchResult, SectionDraft
        sections = [SectionOutline.from_dict(s) for s in state.get("outline", [])]
        drafts = {t: SectionDraft.from_dict(d) if isinstance(d, dict) else d for t, d in state.get("drafts", {}).items()}
        research = {t: [SearchResult.from_dict(r) for r in res] for t, res in state.get("research", {}).items()}

        from src.config import get_config
        from src.llm.client import get_llm_client
        config = get_config()
        llm = get_llm_client(model_override=config.llm.editor_model)
        editor = EditorAgent(llm_client=llm)

        # Optimization: Only review sections that need it
        fb_dict = {}
        for s in sections:
            # If we just revised a specific section, only re-review that one
            revised_section = state.get("section_being_revised")
            if revised_section and s.title != revised_section:
                continue # Skip others, we already have their feedback
            
            draft = drafts.get(s.title)
            if draft:
                fb_dict[s.title] = editor.review(state["topic"], draft, s, research.get(s.title, []))
        
        # Merge new feedback with existing feedback in state
        all_fb = state.get("all_feedback", {})
        all_fb.update({t: f.to_dict() for t, f in fb_dict.items()})
        
        # Check if ANY section in the full list still needs rewrite
        from src.state import EditorFeedback
        needs_rev = False
        target_title = None
        target_fb = None

        # Extract current iteration count from state
        iteration_count = state.get("iteration_count", 0)

        # Safety: Check if we've already hit the global iteration limit
        if iteration_count >= state.get("max_iterations", 2):
            logger.info(f"Max iterations ({iteration_count}) reached. Forcing compilation.")
            return update_state(state, current_step="compiling")

        for s in sections:
            fb_data = all_fb.get(s.title)
            if fb_data:
                fb = EditorFeedback.from_dict(fb_data)
                # Only rewrite if it's a MAJOR issue or LLM explicitly says so
                if fb.needs_rewrite or fb.severity == "major":
                    needs_rev = True
                    target_title = s.title
                    target_fb = fb_data
                    break
        
        if needs_rev:
            return update_state(state, all_feedback=all_fb, current_feedback=target_fb, section_being_revised=target_title, current_step="revision")
        
        return update_state(state, all_feedback=all_fb, current_step="compiling")
    except Exception as e:
        logger.error(f"Editing failed: {e}")
        return add_error(state, f"Editing failed: {e}")

def revision_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """Revision node: Rewrite based on feedback."""
    try:
        from src.state import SectionDraft, SearchResult, EditorFeedback
        title = state.get("section_being_revised")
        draft = SectionDraft.from_dict(state["drafts"][title])
        feedback = EditorFeedback.from_dict(state["current_feedback"])
        research = [SearchResult.from_dict(r) for r in state["research"].get(title, [])]

        from src.config import get_config
        from src.llm.client import get_llm_client
        config = get_config()
        llm = get_llm_client(model_override=config.llm.writer_model)
        writer = WriterAgent(llm_client=llm)

        revised = writer.revise_section(state["topic"], draft, str(feedback.issues), research)
        drafts = dict(state["drafts"])
        drafts[title] = revised.to_dict()
        
        return update_state(state, drafts=drafts, iteration_count=state.get("iteration_count", 0) + 1, section_being_revised=None, current_feedback=None, current_step="editing")
    except Exception as e:
        logger.error(f"Revision failed: {e}")
        return add_error(state, f"Revision failed: {e}")

def compilation_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """Compilation node: Generate final document."""
    try:
        logger.info("Starting compilation node")
        from src.state import SectionDraft, SectionOutline
        drafts = {t: SectionDraft.from_dict(d) if isinstance(d, dict) else d for t, d in state.get("drafts", {}).items()}
        sections = [SectionOutline.from_dict(s) if isinstance(s, dict) else s for s in state.get("outline", [])]
        ordered = [drafts[s.title] for s in sections if s.title in drafts]

        compiler = DocumentCompiler()
        res = compiler.compile(sections=ordered, title=state.get("topic", "Document"), formats=["markdown", "docx"], metadata={"topic": state.get("topic"), "word_count": get_total_word_count(state), "sections": len(ordered)})

        final_doc = f"# {state.get('topic', 'Document')}\n\n" + "\n\n".join([f"## {d.section_title}\n\n{d.content}" for d in ordered])
        return update_state(state, final_document=final_doc, current_step="completed")
    except Exception as e:
        logger.error(f"Compilation failed: {e}")
        return add_error(state, f"Compilation failed: {e}")

def error_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """Error node: Handle failures."""
    logger.error(f"Workflow errors: {state.get('errors', [])}")
    return update_state(state, current_step="error")

def should_continue_to_research(state: Dict[str, Any]) -> str:
    """Check if should proceed to research."""
    if state.get("errors"): return "error"
    return "research"

def should_continue_to_editing(state: Dict[str, Any]) -> str:
    """Check next step after editing."""
    if state.get("errors"): return "error"
    return state.get("current_step", "compiling")
