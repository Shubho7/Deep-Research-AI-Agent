from typing import Dict, List, Any, Optional
import traceback
import re
from agents.base_agent import BaseAgent
from utils.config import CITATION_MODEL, DEFAULT_CITATION_STYLE

class CitationAgent(BaseAgent):
    """
    Agent responsible for formatting and validating sources in the research document.
    """
    
    def __init__(
        self,
        name: str = "Citation Agent",
        description: str = "Formats and validates sources in research documents",
        model_name: str = CITATION_MODEL,
        api_key: Optional[str] = None,
        temperature: float = 0.0,  # Low temperature for precise citation formatting
        citation_style: str = DEFAULT_CITATION_STYLE
    ):
        """
        Initialize the citation agent.
        
        Args:
            name: The name of the agent
            description: A short description of the agent's purpose
            model_name: The name of the LLM model to use
            api_key: The API key
            temperature: The temperature setting for the LLM
            citation_style: The citation style to use (e.g., "APA", "MLA")
        """
        print(f"Initializing {name} with {model_name}")
        super().__init__(name, description, model_name, api_key, temperature)
        self.citation_style = citation_style
        
        # Create the citation extraction chain
        print("Creating citation extraction chain...")
        self.extraction_chain = self.create_chain(
            """
            You are a professional citation analyst tasked with extracting and analyzing all citations in a research document.
            
            Research draft:
            {draft}
            
            Your task is to:
            1. Extract all citations and references found in the document
            2. List each source with its associated URL
            3. Note any places where a factual claim is made but lacks a citation
            
            Format your response as a structured list of all sources found, with URLs.
            For each citation, include:
            - The exact citation text as it appears in the document
            - The complete URL
            - The context in which it was used (brief excerpt)
            
            Also separately list any claims that appear to need citation but don't have one.
            """,
            output_key="citation_analysis"
        )
        
        # Create the citation formatting chain
        print("Creating citation formatting chain...")
        self.formatting_chain = self.create_chain(
            f"""
            You are a professional citation editor tasked with standardizing and improving the citation format in a research document.
            
            Research topic: {{research_topic}}
            
            Original draft:
            {{draft}}
            
            Citation analysis:
            {{citation_analysis}}
            
            Your task is to:
            1. Standardize all citations to use {self.citation_style} format
            2. Add citations for claims that need them, based on the research synthesis
            3. Ensure each citation is properly linked to its source
            4. Add a "References" section at the end of the document with a numbered list of all sources
            5. Replace inline citation URLs with reference numbers or standardized in-text citations that link to the References section
            
            Research synthesis for reference:
            {{research_synthesis}}
            
            Provide the complete revised document with properly formatted citations and a References section.
            Maintain the original structure and content of the document while improving the citation format.
            """,
            output_key="formatted_draft"
        )
        
        # Create the validation chain
        print("Creating citation validation chain...")
        self.validation_chain = self.create_chain(
            """
            You are a citation validator tasked with ensuring the accuracy and validity of sources in a research document.
            
            Formatted draft with citations:
            {formatted_draft}
            
            Your task is to:
            1. Verify that all URLs in the References section are properly formatted
            2. Check that all reference numbers in the text correctly link to the References section
            3. Ensure there are no broken or incomplete citations
            4. Confirm that the References section contains all sources cited in the text
            
            Provide a brief validation report. If issues are found, describe them clearly.
            If the validation passes, simply state that all citations appear to be properly formatted.
            
            Then provide the final validated document, with any necessary corrections applied.
            """,
            output_key="validation_result"
        )
        print(f"{name} initialization complete.")
    
    def extract_citations(self, draft: str) -> str:
        """
        Extract and analyze citations from the draft.
        
        Args:
            draft: The draft to analyze
            
        Returns:
            A citation analysis report
        """
        print(f"Extracting citations from draft")
        try:
            result = self.extraction_chain({
                "draft": draft
            })
            
            print("Citation extraction completed successfully.")
            return result["citation_analysis"]
        except Exception as e:
            print(f"Error extracting citations: {e}")
            traceback.print_exc()
            return f"Error extracting citations: {str(e)}"
    
    def format_citations(self, research_topic: str, research_synthesis: str, draft: str, citation_analysis: str) -> str:
        """
        Format citations in the draft.
        
        Args:
            research_topic: The research topic
            research_synthesis: The research synthesis
            draft: The draft to format
            citation_analysis: The citation analysis
            
        Returns:
            A draft with formatted citations
        """
        print(f"Formatting citations for topic: '{research_topic}'")
        try:
            result = self.formatting_chain({
                "research_topic": research_topic,
                "draft": draft,
                "citation_analysis": citation_analysis,
                "research_synthesis": research_synthesis
            })
            
            print("Citation formatting completed successfully.")
            return result["formatted_draft"]
        except Exception as e:
            print(f"Error formatting citations: {e}")
            traceback.print_exc()
            return draft  # Return the original draft if formatting fails
    
    def validate_citations(self, formatted_draft: str) -> Dict[str, str]:
        """
        Validate citations in the formatted draft.
        
        Args:
            formatted_draft: The draft with formatted citations
            
        Returns:
            A validation report and the final validated draft
        """
        print(f"Validating citations")
        try:
            result = self.validation_chain({
                "formatted_draft": formatted_draft
            })
            
            validation_result = result["validation_result"]
            
            # Split the validation result to extract the report and the validated document
            # First check if we can find clear delimiters
            if "## Validation Report" in validation_result and "## Final Document" in validation_result:
                parts = validation_result.split("## Final Document", 1)
                validation_report = parts[0].replace("## Validation Report", "").strip()
                validated_draft = parts[1].strip()
            else:
                # If no clear delimiters, use regex to try to find the document part
                # Look for markdown headings, horizontal rules, or other potential delimiters
                match = re.search(r'(\n\s*?-{3,}|\n\s*?#{1,6}\s+|\n\s*?\*{3,}|\n\s*?_{3,})\s*?\n', validation_result)
                if match:
                    split_point = match.start()
                    validation_report = validation_result[:split_point].strip()
                    validated_draft = validation_result[match.end():].strip()
                else:
                    # If we can't clearly identify parts, assume first paragraph is report and rest is document
                    paragraphs = validation_result.split('\n\n', 1)
                    if len(paragraphs) > 1:
                        validation_report = paragraphs[0].strip()
                        validated_draft = paragraphs[1].strip()
                    else:
                        # If all else fails, return the whole thing as the document
                        validation_report = "No validation issues found."
                        validated_draft = validation_result
            
            print("Citation validation completed successfully.")
            return {
                "validation_report": validation_report,
                "validated_draft": validated_draft
            }
        except Exception as e:
            print(f"Error validating citations: {e}")
            traceback.print_exc()
            return {
                "validation_report": f"Error validating citations: {str(e)}",
                "validated_draft": formatted_draft  # Return the input draft if validation fails
            }
    
    def run(self, research_topic: str, research_synthesis: str, draft: str) -> Dict[str, Any]:
        """
        Run the citation agent to format and validate sources.
        
        Args:
            research_topic: The research topic
            research_synthesis: The research synthesis
            draft: The draft to process
            
        Returns:
            A dictionary containing the citation analysis, formatted draft, and validation report
        """
        print(f"\n=== Starting citation processing for topic: '{research_topic}' ===")
        try:
            # Extract citations
            print("Extracting and analyzing citations...")
            citation_analysis = self.extract_citations(draft)
            self.add_to_memory({"type": "citation_analysis", "content": citation_analysis})
            
            # Format citations
            print("Formatting citations...")
            formatted_draft = self.format_citations(research_topic, research_synthesis, draft, citation_analysis)
            self.add_to_memory({"type": "formatted_draft", "content": formatted_draft})
            
            # Validate citations
            print("Validating citations...")
            validation_result = self.validate_citations(formatted_draft)
            self.add_to_memory({"type": "validation_result", "content": validation_result})
            
            print("Citation processing completed successfully.")
            return {
                "research_topic": research_topic,
                "citation_analysis": citation_analysis,
                "formatted_draft": formatted_draft,
                "validation_report": validation_result["validation_report"],
                "final_draft": validation_result["validated_draft"]
            }
        except Exception as e:
            print(f"Error in citation agent: {e}")
            traceback.print_exc()
            return {
                "research_topic": research_topic,
                "citation_analysis": f"Error during citation analysis: {str(e)}",
                "formatted_draft": draft,
                "validation_report": f"Error: {str(e)}",
                "final_draft": draft,  # Return the original draft if process fails
                "error": str(e)
            } 