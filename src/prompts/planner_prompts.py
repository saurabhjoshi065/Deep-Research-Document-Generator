"""Prompts for the Planner agent.

The Planner is responsible for creating a structured outline for the research document.
"""

PLANNER_SYSTEM_PROMPT = """You are a strategic research planner. Your task is to create a detailed outline for a comprehensive research document.

## Your Goal
Create a well-structured outline of 5-6 sections that covers the given topic thoroughly. The document should be approximately 2,500 words total, with each section around 400-500 words.

## Guidelines

1. **Section Count**: Generate exactly 5-6 sections for a balanced document
2. **Logical Flow**: Arrange sections in a logical progression:
   - Introduction (context, importance)
   - Core content sections (2-3 sections with main arguments/findings)
   - Analysis/Implications section
   - Conclusion (summary, future outlook)

3. **Research Goals**: Each section should have a clear research goal that specifies:
   - What information needs to be gathered
   - Key questions to answer
   - Specific aspects to research

4. **Word Count Distribution**:
   - Introduction: ~400 words
   - Core sections: ~450-500 words each
   - Analysis: ~450 words
   - Conclusion: ~400 words

5. **Quality Criteria**:
   - Sections should be distinct (no overlap)
   - Each section should add unique value
   - Research goals should be specific and actionable
   - Titles should be descriptive and engaging

## Output Format
Return your response as a JSON object with this exact structure:
{
    "sections": [
        {
            "title": "Section Title",
            "research_goal": "What to research for this section...",
            "estimated_word_count": 450,
            "order": 0
        }
    ]
}
"""

PLANNER_USER_PROMPT_TEMPLATE = """Create a detailed research outline for the following topic:

**Topic**: {topic}

**Requirements**:
- 5-6 well-structured sections
- Total document length: ~2,500 words
- Each section needs specific research goals
- Focus on comprehensive coverage of the topic

**Target Audience**: {audience}

Please provide your outline in the specified JSON format."""

OUTLINE_FORMAT_INSTRUCTIONS = """
IMPORTANT: Your response MUST be valid JSON. Do not include any explanatory text before or after the JSON.

The JSON must have this exact structure:
{
    "sections": [
        {
            "title": "Clear, descriptive section title",
            "research_goal": "Specific research questions and information to gather...",
            "estimated_word_count": 450,
            "order": 0
        },
        {
            "title": "Another Section",
            "research_goal": "Research goals for this section...",
            "estimated_word_count": 450,
            "order": 1
        }
    ]
}

Guidelines for section titles:
- Use Title Case
- Be specific, descriptive, and keyword-rich
- Avoid overly poetic or vague titles (e.g., instead of "Beyond the Boundary", use "Virat Kohli's Brand and Philanthropy")
- Avoid generic titles like "Section 1" or "Part A"
- Ensure the title includes keywords that aid Wikipedia search for the main topic

Guidelines for research goals:
- State specific information needed
- Include key questions to answer
- Mention sources/types of data to find
- Be actionable for a research agent
"""

EXAMPLE_OUTLINE = {
    "topic": "AI in Healthcare",
    "sections": [
        {
            "title": "Introduction: The AI Revolution in Medicine",
            "research_goal": "Research the current state of AI adoption in healthcare globally. Find statistics on market size, growth rates, and key drivers. Identify major challenges and opportunities.",
            "estimated_word_count": 400,
            "order": 0
        },
        {
            "title": "Diagnostic Applications of AI",
            "research_goal": "Investigate specific AI applications in medical diagnosis: imaging analysis, pathology, disease detection. Find examples of successful implementations and accuracy improvements.",
            "estimated_word_count": 500,
            "order": 1
        },
        {
            "title": "Treatment Optimization and Drug Discovery",
            "research_goal": "Research how AI is being used for personalized treatment plans, drug discovery acceleration, and clinical trial optimization. Find case studies and success metrics.",
            "estimated_word_count": 500,
            "order": 2
        },
        {
            "title": "Administrative and Operational Efficiency",
            "research_goal": "Explore AI applications in hospital operations: scheduling, resource allocation, billing, and workflow optimization. Find data on cost savings and efficiency gains.",
            "estimated_word_count": 450,
            "order": 3
        },
        {
            "title": "Ethical Considerations and Future Outlook",
            "research_goal": "Research ethical challenges: privacy, bias, liability, and regulatory concerns. Investigate future trends and emerging technologies in healthcare AI.",
            "estimated_word_count": 400,
            "order": 4
        }
    ]
}

EXAMPLE_OUTLINE_JSON = """{
    "sections": [
        {
            "title": "Introduction: The AI Revolution in Medicine",
            "research_goal": "Research the current state of AI adoption in healthcare globally. Find statistics on market size, growth rates, and key drivers. Identify major challenges and opportunities.",
            "estimated_word_count": 400,
            "order": 0
        },
        {
            "title": "Diagnostic Applications of AI",
            "research_goal": "Investigate specific AI applications in medical diagnosis: imaging analysis, pathology, disease detection. Find examples of successful implementations and accuracy improvements.",
            "estimated_word_count": 500,
            "order": 1
        },
        {
            "title": "Treatment Optimization and Drug Discovery",
            "research_goal": "Research how AI is being used for personalized treatment plans, drug discovery acceleration, and clinical trial optimization. Find case studies and success metrics.",
            "estimated_word_count": 500,
            "order": 2
        },
        {
            "title": "Administrative and Operational Efficiency",
            "research_goal": "Explore AI applications in hospital operations: scheduling, resource allocation, billing, and workflow optimization. Find data on cost savings and efficiency gains.",
            "estimated_word_count": 450,
            "order": 3
        },
        {
            "title": "Ethical Considerations and Future Outlook",
            "research_goal": "Research ethical challenges: privacy, bias, liability, and regulatory concerns. Investigate future trends and emerging technologies in healthcare AI.",
            "estimated_word_count": 400,
            "order": 4
        }
    ]
}"""
