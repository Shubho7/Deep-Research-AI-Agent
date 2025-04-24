from typing import Dict, List, Any, Optional
import traceback
from agents.base_agent import BaseAgent
from utils.config import DRAFTING_MODEL

class DraftingAgent(BaseAgent):
    """
    Agent responsible for drafting comprehensive answers based on research.
    """
    
    def __init__(
        self,
        name: str = "Drafting Agent",
        description: str = "Creates structured answers from research",
        model_name: str = DRAFTING_MODEL,
        api_key: Optional[str] = None,
        temperature: float = 0.3,  # Slightly higher temperature for more creative drafting
    ):
        """
        Initialize the drafting agent.
        
        Args:
            name: The name of the agent
            description: A short description of the agent's purpose
            model_name: The name of the LLM model to use
            api_key: The OpenAI API key
            temperature: The temperature setting for the LLM
        """
        print(f"Initializing {name} with model {model_name}")
        super().__init__(name, description, model_name, api_key, temperature)
        
        # Create the drafting chain
        print("Creating drafting chain...")
        self.drafting_chain = self.create_chain(
            """
            You are a professional content writer tasked with creating a comprehensive, 
            well-structured answer based on research findings.
            
            Research topic: {research_topic}
            
            Research synthesis:
            {research_synthesis}
            
            Your task is to create a well-structured answer with the following characteristics:
            1. Clear and engaging introduction that frames the topic
            2. Logically organized body with proper headings and subheadings
            3. Comprehensive coverage of the key aspects of the topic
            4. Evidence-based statements with proper attribution to sources
            5. Balanced presentation of different perspectives where applicable
            6. Thoughtful conclusion that summarizes key insights
            
            Format your answer using markdown for better readability.
            Include citations in the format [Source: URL] where appropriate.
            
            The answer should be comprehensive while being accessible to a general audience.
            """,
            output_key="draft"
        )
        
        # Create the review and improve chain
        print("Creating review and improve chain...")
        self.improve_chain = self.create_chain(
            """
            You are a professional editor tasked with reviewing and improving a draft answer.
            
            Research topic: {research_topic}
            
            Original draft:
            {draft}
            
            Your task is to review the draft and improve it in the following ways:
            1. Check for factual accuracy and consistency
            2. Improve clarity and readability
            3. Ensure logical flow and organization
            4. Enhance the quality of explanations
            5. Add any missing important information
            6. Remove any redundant or irrelevant information
            7. Ensure proper citation and attribution
            
            Provide the improved version while maintaining the overall structure and format of the original.
            """,
            output_key="improved_draft"
        )
        print(f"{name} initialization complete.")
    
    def draft_answer(self, research_topic: str, research_synthesis: str) -> str:
        """
        Draft an initial answer based on the research synthesis.
        
        Args:
            research_topic: The research topic
            research_synthesis: The synthesized research findings
            
        Returns:
            A drafted answer
        """
        print(f"Drafting answer for topic: '{research_topic}'")
        try:
            # The chain is now a callable function, not an object with invoke()
            result = self.drafting_chain({
                "research_topic": research_topic,
                "research_synthesis": research_synthesis
            })
            
            print("Draft created successfully.")
            return result["draft"]
        except Exception as e:
            print(f"Error drafting answer: {e}")
            traceback.print_exc()
            return f"Error creating draft: {str(e)}"
    
    def improve_answer(self, research_topic: str, draft: str) -> str:
        """
        Review and improve the drafted answer.
        
        Args:
            research_topic: The research topic
            draft: The initial draft
            
        Returns:
            An improved version of the draft
        """
        print(f"Improving draft for topic: '{research_topic}'")
        try:
            # The chain is now a callable function, not an object with invoke()
            result = self.improve_chain({
                "research_topic": research_topic,
                "draft": draft
            })
            
            print("Draft improved successfully.")
            return result["improved_draft"]
        except Exception as e:
            print(f"Error improving draft: {e}")
            traceback.print_exc()
            return draft  # Return the original draft if improvement fails
    
    def run(self, research_topic: str, research_synthesis: str, improve: bool = True) -> Dict[str, Any]:
        """
        Run the drafting agent to create an answer.
        
        Args:
            research_topic: The research topic
            research_synthesis: The synthesized research findings
            improve: Whether to run the improvement step
            
        Returns:
            A dictionary containing the drafted answer
        """
        print(f"\n=== Starting drafting for topic: '{research_topic}' ===")
        try:
            # Draft the initial answer
            print("Creating initial draft...")
            draft = self.draft_answer(research_topic, research_synthesis)
            self.add_to_memory({"type": "draft", "content": draft})
            
            # Improve the draft if requested
            final_answer = draft
            if improve:
                print("Improving draft...")
                final_answer = self.improve_answer(research_topic, draft)
                self.add_to_memory({"type": "improved_draft", "content": final_answer})
            
            print("Drafting completed successfully.")
            return {
                "research_topic": research_topic,
                "initial_draft": draft,
                "final_answer": final_answer
            }
        except Exception as e:
            print(f"Error in drafting agent: {e}")
            traceback.print_exc()
            return {
                "research_topic": research_topic,
                "initial_draft": "Error occurred during drafting.",
                "final_answer": f"Error occurred: {str(e)}",
                "error": str(e)
            } 