"""Streamlit UI for Deep Research Document Generator."""

import streamlit as st
import time
from pathlib import Path
from src.graph import create_workflow
from src.state import create_initial_state, get_total_word_count

st.set_page_config(page_title="Deep Research Generator", page_icon="📝", layout="wide")

def main():
    st.title("📝 Deep Research Document Generator")
    st.markdown("Generate high-quality research reports using Wikipedia and DeepSeek.")

    with st.sidebar:
        st.header("Settings")
        topic = st.text_input("Research Topic", placeholder="e.g., Virat Kohli Career")
        sections = st.slider("Number of Sections", 2, 6, 3)
        max_iterations = st.slider("Max Revisions", 1, 3, 2)
        st.divider()
        st.caption("Backend: DeepSeek-V3 (671B) + Wikipedia")

    if st.button("Generate Report", type="primary", disabled=not topic):
        if len(topic) < 3:
            st.error("Topic too short.")
            return

        status_box = st.status("🚀 Initializing Agents...", expanded=True)
        progress_bar = st.progress(0)
        
        state = create_initial_state(topic=topic)
        state["max_iterations"] = max_iterations
        state["sections_count"] = sections
        
        workflow = create_workflow()
        final_state = state

        try:
            for output in workflow.stream(state):
                for node_name, node_state in output.items():
                    final_state = node_state
                    
                    if node_name == "planning":
                        status_box.write("✅ Outline generated successfully.")
                        progress_bar.progress(20)
                    
                    elif node_name == "research":
                        status_box.write("🌐 Wikipedia research complete. Facts gathered.")
                        progress_bar.progress(40)
                    
                    elif node_name == "writing":
                        status_box.write("✍️ Drafting section content...")
                        progress_bar.progress(60)
                    
                    elif node_name == "editing":
                        status_box.write("🔍 Editor is reviewing quality...")
                        progress_bar.progress(80)
                    
                    elif node_name == "revision":
                        status_box.write("🔄 Improving sections based on feedback...")
                        progress_bar.progress(85)
                    
                    elif node_name == "compilation":
                        status_box.write("📚 Compiling final document...")
                        progress_bar.progress(95)

            if final_state.get("current_step") == "error":
                status_box.update(label="❌ Research Failed", state="error")
                st.error(f"Error: {', '.join(final_state.get('errors', []))}")
                return

            status_box.update(label="✨ Research Complete!", state="complete", expanded=False)
            progress_bar.progress(100)

            st.divider()
            st.balloons()
            
            c1, c2, c3 = st.columns(3)
            c1.metric("Topic", topic)
            c2.metric("Total Words", get_total_word_count(final_state))
            c3.metric("Sections", len(final_state.get("drafts", {})))

            st.subheader("Final Report")
            content = final_state.get("final_document", "")
            if content:
                st.markdown(content)
                
                col_dl1, col_dl2 = st.columns(2)
                with col_dl1:
                    st.download_button(
                        label="📥 Download Markdown (.md)",
                        data=content,
                        file_name=f"{topic.lower().replace(' ', '-')}.md",
                        mime="text/markdown",
                        use_container_width=True
                    )
                
                safe_title = "".join(c for c in topic.replace(" ", "-").replace("_", "-") if c.isalnum() or c in "-_").rstrip("-").lower() or "document"
                docx_path = Path("output") / f"{safe_title}.docx"
                
                if docx_path.exists():
                    with open(docx_path, "rb") as f:
                        with col_dl2:
                            st.download_button(
                                label="📥 Download Word (.docx)",
                                data=f,
                                file_name=f"{safe_title}.docx",
                                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                                use_container_width=True
                            )
            else:
                st.warning("No content was generated. Please check logs.")

        except Exception as e:
            status_box.update(label="❌ System Error", state="error")
            st.error(f"An unexpected error occurred: {e}")

if __name__ == "__main__":
    main()
