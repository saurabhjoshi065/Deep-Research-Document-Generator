"""Prompts for the Writer agent.

The Writer creates section drafts based on research data.
"""

WRITER_SYSTEM_PROMPT = """You are a professional research writer. Your writing is:
- Formal and objective in tone
- Evidence-based with proper citations
- Structured with clear arguments
- Precise in terminology and definitions
- Comprehensive with thorough analysis

Guidelines:
- Use third-person perspective
- Include citations as [Source: URL or Title]
- Present balanced viewpoints
- Support claims with evidence"""

SECTION_WRITING_PROMPT = """Write a section for a research document.

## Document Topic
The overall document is about: **{topic}**

## Section Information
**Title**: {section_title}
**Target Word Count**: ~{target_words} words (currently {word_count})

## Research Data
{research_data}

## Writing Requirements

1. **Content Relevance**:
   - **CRITICAL**: Your content MUST stay on the document topic: **{topic}**.
   - Review the provided Research Data carefully. Some of it may be irrelevant or from unrelated subjects (e.g., different people, sports, or events).
   - **ONLY** use information that directly relates to **{topic}** and the section **{section_title}**.
   - If research data is irrelevant, **IGNORE IT**. Do not try to include it.
   - Provide depth and analysis, not just surface facts.
   - Include specific examples, numbers, and dates where available.

2. **Structure**:
   - Start with a strong topic sentence.
   - Develop 2-3 main points with supporting evidence.
   - Use transitions between ideas.
   - End with a concluding sentence.

3. **Citations**:
   - Cite sources inline as [Source: URL or Title].
   - Use at least 3-5 different sources if available in the relevant data.
   - Distribute citations throughout the section.

## Output
Write only the section content. Do not include:
- The section title as a heading
- Meta-commentary about what you're doing
- Questions to the user
- Placeholder text

Provide complete, publication-ready content."""

CITATION_INSTRUCTIONS = """
## Citation Format

Include citations naturally in the text:
- For web sources: [Source: URL]
- For research papers: [Source: Author et al., Year]
- For organizations: [Source: Organization Name]

Examples:
- "The market grew by 23% last year [Source: https://example.com/report]."
- "According to recent studies [Source: Smith et al., 2024], this trend continues."
- "The WHO reports [Source: World Health Organization] that..."
"""
