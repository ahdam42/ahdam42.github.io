RELEVANCE_QUESTION = 'Does the article discuss topics related to autonomous driving or topics that can aid in understanding autonomous driving?'
from typing import List

class PromptService:
    @staticmethod
    def create_relevance_prompt(candidate_summary):
        return f"""Question:  {RELEVANCE_QUESTION}

        ### ARTICLE SUMMARY START ###
        {candidate_summary}
        ### ARTICLE SUMMARY END ###

        Please provide a clear and concise answer: 'Yes' or 'No'. Only 'yes' or 'no' text in answer is accepted."""
    
    @staticmethod
    def create_summary_prompt(text):
        return f"""
        Provide a comprehensive, structured summary of the article that addresses the following elements:  
        
        1. **Title**: State the exact title of the article (if available).  
        2. **Scope and Field**: Identify the article’s domain, research field, and overarching focus.  
        3. **Methodology**: Explain *what* was investigated and *how* (methods, approaches, or frameworks used).  
        4. **Key Results**: Summarize the findings, including quantitative/qualitative outcomes.  
        5. **Critical Analysis**: Highlight limitations, uncertainties, or potential biases in the results.  
        6. **Broader Context**: Discuss the article’s implications for its field or real-world applications.  

        Ensure clarity and conciseness while covering all critical aspects. Avoid unnecessary details.  

        ### ARTICLE START ###  
        {text}  
        ### ARTICLE END ###  

        Summary:"""
    
    @staticmethod
    def create_partial_prompt(question: str, chunk_text: str, part: int, total: int) -> str:
        """General-purpose chunk analysis prompt"""
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
    def create_chunk_aggregation_prompt(group: List[str], group_number: int) -> str:
        """Generic chunk group aggregation prompt"""
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
    def create_article_aggregation_prompt(group: List, group_number: int) -> str:
        """Generic article group aggregation prompt"""
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