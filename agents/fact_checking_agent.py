"""
Fact-checking agent that verifies information accuracy.
"""
from typing import Dict, List, Any, Optional
import traceback
from agents.base_agent import BaseAgent
from utils.config import FACT_CHECK_MODEL

class FactCheckingAgent(BaseAgent):
    """
    Agent responsible for verifying the accuracy of information in the draft.
    """
    
    def __init__(
        self,
        name: str = "Fact-Checking Agent",
        description: str = "Verifies information accuracy in research documents",
        model_name: str = FACT_CHECK_MODEL,
        api_key: Optional[str] = None,
        temperature: float = 0.0,  # Low temperature for factual verification
    ):
        """
        Initialize the fact-checking agent.
        
        Args:
            name: The name of the agent
            description: A short description of the agent's purpose
            model_name: The name of the LLM model to use
            api_key: The API key
            temperature: The temperature setting for the LLM
        """
        print(f"Initializing {name} with {model_name}")
        super().__init__(name, description, model_name, api_key, temperature)
        
        # Create the fact-checking chain
        print("Creating fact-checking chain...")
        self.fact_checking_chain = self.create_chain(
            """
            You are a professional fact-checker tasked with verifying the accuracy of information 
            in a research draft based on the original research findings.
            
            Research topic: {research_topic}
            
            Original research synthesis:
            {research_synthesis}
            
            Draft to verify:
            {draft}
            
            Your task is to:
            1. Identify any factual inaccuracies or unsupported claims in the draft
            2. Assess whether the draft correctly represents the information from the research synthesis
            3. Check for any misleading statements, exaggerations, or oversimplifications
            4. Verify that the citations are used correctly and support the associated claims
            
            For each issue identified, provide:
            - The specific statement or claim that is problematic
            - The nature of the issue (inaccuracy, unsupported claim, misrepresentation, etc.)
            - The correct information based on the research synthesis
            
            Do not flag stylistic issues or matters of opinion - focus only on factual accuracy.
            If no issues are found, state that the draft appears to be factually accurate based on the provided research synthesis.
            
            Format your fact-check report using markdown for better readability.
            """,
            output_key="fact_check_report"
        )
        
        # Create the correction chain
        print("Creating correction chain...")
        self.correction_chain = self.create_chain(
            """
            You are a professional editor tasked with correcting factual inaccuracies in a research draft.
            
            Research topic: {research_topic}
            
            Original draft:
            {draft}
            
            Fact check report:
            {fact_check_report}
            
            Your task is to:
            1. Carefully review the fact check report
            2. Modify the draft to correct all identified factual inaccuracies
            3. Ensure the corrections maintain the flow and readability of the document
            4. Add appropriate citations for any new factual claims
            5. Preserve the original structure and style of the document
            
            Provide the corrected version of the draft, maintaining the overall format and structure.
            If the fact check report indicates no issues, return the original draft unchanged.
            """,
            output_key="corrected_draft"
        )
        print(f"{name} initialization complete.")
    
    def check_facts(self, research_topic: str, research_synthesis: str, draft: str) -> str:
        """
        Perform fact-checking on the draft.
        
        Args:
            research_topic: The research topic
            research_synthesis: The original research synthesis
            draft: The draft to fact-check
            
        Returns:
            A fact-check report
        """
        print(f"Fact-checking draft for topic: '{research_topic}'")
        try:
            result = self.fact_checking_chain({
                "research_topic": research_topic,
                "research_synthesis": research_synthesis,
                "draft": draft
            })
            
            print("Fact-checking completed successfully.")
            return result["fact_check_report"]
        except Exception as e:
            print(f"Error during fact-checking: {e}")
            traceback.print_exc()
            return f"Error during fact-checking: {str(e)}"
    
    def correct_draft(self, research_topic: str, draft: str, fact_check_report: str) -> str:
        """
        Correct the draft based on fact-checking results.
        
        Args:
            research_topic: The research topic
            draft: The draft to correct
            fact_check_report: The fact-check report
            
        Returns:
            A corrected draft
        """
        print(f"Correcting draft for topic: '{research_topic}'")
        try:
            result = self.correction_chain({
                "research_topic": research_topic,
                "draft": draft,
                "fact_check_report": fact_check_report
            })
            
            print("Draft correction completed successfully.")
            return result["corrected_draft"]
        except Exception as e:
            print(f"Error correcting draft: {e}")
            traceback.print_exc()
            return draft  # Return the original draft if correction fails
    
    def run(self, research_topic: str, research_synthesis: str, draft: str) -> Dict[str, Any]:
        """
        Run the fact-checking agent to verify and correct the draft.
        
        Args:
            research_topic: The research topic
            research_synthesis: The original research synthesis
            draft: The draft to fact-check and correct
            
        Returns:
            A dictionary containing the fact-check report and corrected draft
        """
        print(f"\n=== Starting fact-checking for topic: '{research_topic}' ===")
        try:
            # Perform fact-checking
            print("Checking facts in the draft...")
            fact_check_report = self.check_facts(research_topic, research_synthesis, draft)
            self.add_to_memory({"type": "fact_check_report", "content": fact_check_report})
            
            # Correct the draft based on fact-checking
            print("Correcting the draft...")
            corrected_draft = self.correct_draft(research_topic, draft, fact_check_report)
            self.add_to_memory({"type": "corrected_draft", "content": corrected_draft})
            
            print("Fact-checking and correction completed successfully.")
            return {
                "research_topic": research_topic,
                "fact_check_report": fact_check_report,
                "corrected_draft": corrected_draft
            }
        except Exception as e:
            print(f"Error in fact-checking agent: {e}")
            traceback.print_exc()
            return {
                "research_topic": research_topic,
                "fact_check_report": f"Error during fact-checking: {str(e)}",
                "corrected_draft": draft,  # Return the original draft if process fails
                "error": str(e)
            } 