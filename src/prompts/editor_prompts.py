"""Prompts for the Editor agent.

The Editor reviews and improves document sections.
"""

EDITOR_SYSTEM_PROMPT = """You are an expert editor reviewing a research document. Your goal is to ensure high quality, accuracy, and professional tone."""

EDITOR_REVIEW_PROMPT = """Review the following research section.

## Section Information
**Title**: {section_title}
**Target Word Count**: {target_words} words
**Current Word Count**: {word_count} words

## Section Content
{content}

## Research Context
{research_context}

## Evaluation Criteria
1. **Topic Relevance**: Does the content stay strictly focused on the main topic (**{topic}**)? Flag any "context drifting" where unrelated subjects (different people, sports, events) are discussed.
2. **Accuracy**: Does it accurately reflect the relevant research data?
3. **Clarity**: Is it well-written, professional, and easy to understand?
4. **Citations**: Are sources properly cited using [Source: URL]?
5. **Depth**: Is there enough detail given the word count?

## Output Format

Return your review as JSON:
```json
{{
    "issues": [
        "Issue 1: Description (e.g., Context drifting: Section discusses American football which is unrelated to Virat Kohli)",
        "Issue 2: ..."
    ],
    "suggestions": [
        "Suggestion 1: Remove irrelevant content about X and replace with facts about {topic}...",
        "Suggestion 2: ..."
    ],
    "needs_rewrite": true/false,
    "severity": "minor|moderate|major"
}}
```

Use `needs_rewrite: true` and `severity: "major"` if the section has significant irrelevant content or hallucinations."""

EDITOR_REWRITE_PROMPT = """Rewrite the following section based on the provided feedback and research data.

## Section Title
{section_title}

## Original Content
{content}

## Feedback to Address
{feedback}

## Research Context
{research_context}

## Requirements
- Address all identified issues
- Maintain a professional, research-oriented tone
- Keep all valid citations [Source: URL]
- Aim for approximately {word_count} words
"""

CROSS_SECTION_REVIEW_PROMPT = """Review the entire research document for consistency and flow.

## Document Outline
{section_titles}

## Full Content
{full_content}

## Evaluation Criteria
- **Consistency**: Are terms and tone consistent?
- **Redundancy**: Are there repeating facts?
- **Flow**: Does the document transition well between sections?

## Output Format

```json
{{
    "consistency_issues": ["Issue 1...", "Issue 2..."],
    "flow_issues": ["Issue 1...", "Issue 2..."],
    "redundancies": ["Redundancy 1...", "Redundancy 2..."],
    "recommendations": ["Rec 1...", "Rec 2..."],
    "overall_quality": "excellent|good|fair|needs_work"
}}
```"""
