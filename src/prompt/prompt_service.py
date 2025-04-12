"""Module containing prompt generation services for autonomous driving articles."""

RELEVANCE_QUESTION = (
    "Does the article discuss topics related to autonomous driving "
    "or topics that can aid in understanding autonomous driving?"
)


class PromptService:
    """A service class for generating various types of prompts related to article analysis."""

    @staticmethod
    def create_relevance_prompt(candidate_summary: str) -> str:
        """
        Generate a prompt to determine article relevance to autonomous driving.

        Args:
            candidate_summary: Summary text to evaluate for relevance

        Returns:
            Formatted relevance check prompt

        """
        return f"""Question:  {RELEVANCE_QUESTION}

        ### ARTICLE SUMMARY START ###
        {candidate_summary}
        ### ARTICLE SUMMARY END ###

        Please provide a clear and concise answer: 'Yes' or 'No'. Only 'yes' or 'no' text in answer is accepted."""

    @staticmethod
    def create_summary_prompt(text: str) -> str:
        """
        Generate a structured article summary prompt.

        Args:
            text: Article content to summarize

        Returns:
            Formatted summary generation prompt

        """
        return f"""
        Provide a comprehensive, structured summary of the article that addresses the following elements:

        1. **Title**: State the exact title of the article (if available).
        2. **Scope and Field**: Identify the article's domain, research field, and overarching focus.
        3. **Methodology**: Explain *what* was investigated and *how* (methods, approaches, or frameworks used).
        4. **Key Results**: Summarize the findings, including quantitative/qualitative outcomes.
        5. **Critical Analysis**: Highlight limitations, uncertainties, or potential biases in the results.
        6. **Broader Context**: Discuss the article's implications for its field or real-world applications.

        Ensure clarity and conciseness while covering all critical aspects. Avoid unnecessary details.

        ### ARTICLE START ###
        {text}
        ### ARTICLE END ###

        Summary:"""

    @staticmethod
    def create_partial_prompt(question: str, chunk_text: str, part: int, total: int) -> str:
        """
        Generate a prompt for analyzing document chunks.

        Args:
            question: Research question to focus on
            chunk_text: Text excerpt from document
            part: Current section number
            total: Total number of sections

        Returns:
            Formatted chunk analysis prompt

        """
        return f"""Analyze this document section (Part {part} of {total}).
        Focus on key elements relevant to: {question}

        Document Excerpt:
        {chunk_text}

        Guidelines:
        1. Identify main concepts and relationships
        2. Note methodological approaches
        3. Highlight unique findings
        4. Mention limitations or gaps

        Structured Analysis:"""

    @staticmethod
    def create_chunk_aggregation_prompt(group: list[str], group_number: int) -> str:
        """
        Aggregate analysis from multiple document chunks into a synthesized prompt.

        Args:
            group: List of document sections
            group_number: Identifier for the group

        Returns:
            Formatted synthesis prompt

        """
        return f"""
            Synthesize key points from {len(group)} document sections:
            Sections Group {group_number}:
            {"".join([f"--- Section {i + 1} ---{text}" for i, text in enumerate(group)])}

            Synthesis Guidelines:
            1. Remove redundant information
            2. Preserve unique findings
            3. Highlight patterns and contradictions
            4. Maintain page references

            Consolidated Analysis:"""

    @staticmethod
    def create_article_aggregation_prompt(group: list, group_number: int) -> str:
        """
        Integrate analyses from multiple articles into a comprehensive prompt.

        Args:
            group: List of documents or aggregated sections
            group_number: Identifier for the group

        Returns:
            Formatted integration prompt

        """
        sections = []
        for i, item in enumerate(group, 1):
            if isinstance(item, tuple):
                doc_id, content = item
                sections.append(f"--- Document {doc_id} ---{content}")
            else:
                sections.append(f"--- Aggregated Section {i} ---{item}")

        return f"""Integrate findings from {len(group)} research documents:

            Documents Group {group_number}:
            {sections}

            Integration Guidelines:
            1. Compare methodologies
            2. Identify common patterns
            3. Note divergent results
            4. Highlight innovations
            5. Maintain document references

            Integrated Analysis:"""
