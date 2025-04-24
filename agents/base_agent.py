from typing import Dict, List, Any, Optional, Callable
import traceback
from langchain.prompts import PromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.schema.runnable import RunnablePassthrough, RunnableSequence
from utils.config import DEFAULT_MODEL, GOOGLE_API_KEY, FALLBACK_MODELS

class BaseAgent:
    """
    Base agent class that all specific agents will inherit from.
    """
    
    def __init__(
        self,
        name: str,
        description: str,
        model_name: str = DEFAULT_MODEL,
        api_key: Optional[str] = None,
        temperature: float = 0.0,
    ):
        """
        Initialize the base agent.
        
        Args:
            name: The name of the agent
            description: A short description of the agent's purpose
            model_name: The name of the LLM model to use
            api_key: The Google API key (defaults to config)
            temperature: The temperature setting for the LLM
        """
        self.name = name
        self.description = description
        self.model_name = model_name
        self.api_key = api_key or GOOGLE_API_KEY
        self.temperature = temperature
        
        # Try to initialize the LLM with the primary model
        self.llm = self._initialize_llm(model_name)
        
        # If primary model fails, try fallback models
        if self.llm is None:
            print(f"Failed to initialize {model_name}. Trying fallback models...")
            for fallback_model in FALLBACK_MODELS:
                if fallback_model != model_name:  
                    print(f"Trying fallback model: {fallback_model}")
                    self.llm = self._initialize_llm(fallback_model)
                    if self.llm is not None:
                        self.model_name = fallback_model
                        print(f"Successfully initialized fallback model: {fallback_model}")
                        break
            
            if self.llm is None:
                print("ERROR: Failed to initialize any model. Agent will not function properly.")
        
        # Initialize an empty memory for the agent
        self.memory = []
    
    def _initialize_llm(self, model_name: str) -> Optional[ChatGoogleGenerativeAI]:
        """
        Initialize an LLM with the given model name.
        
        Args:
            model_name: The name of the model to initialize
            
        Returns:
            The initialized LLM, or None if initialization failed
        """
        try:
            print(f"Initializing {self.name} with {model_name}")
            llm = ChatGoogleGenerativeAI(
                model=model_name,
                google_api_key=self.api_key,
                temperature=self.temperature,
                # Removed deprecated parameter: convert_system_message_to_human=True
                safety_settings={
                    1: 0,  # HARM_CATEGORY_HARASSMENT: BLOCK_NONE
                    2: 0,  # HARM_CATEGORY_HATE_SPEECH: BLOCK_NONE
                    3: 0,  # HARM_CATEGORY_SEXUALLY_EXPLICIT: BLOCK_NONE
                    4: 0   # HARM_CATEGORY_DANGEROUS_CONTENT: BLOCK_NONE
                },
                generation_config={"response_mime_type": "text/plain"}
            )
            
            # Test the model with a simple prompt to see if it works
            try:
                print(f"Testing connection to {model_name}...")
                test_response = llm.invoke("Respond with 'ok' if you can read this message.")
                if hasattr(test_response, 'content') and test_response.content:
                    print(f"{model_name} initialized.")
                    return llm
                else:
                    print(f"{model_name} initialized but test failed: empty response")
                    return None
            except Exception as e:
                print(f"Error testing model {model_name}: {e}")
                return None
        except Exception as e:
            print(f"Error initializing model {model_name}: {e}")
            return None
    
    def create_chain(self, prompt_template: str, output_key: str = "output") -> Callable:
        """
        Create a runnable chain with the given prompt template.
        
        Args:
            prompt_template: The prompt template string
            output_key: The key to use for the output
            
        Returns:
            A callable runnable sequence
        """
        if self.llm is None:
            print(f"WARNING: {self.name} has no initialized LLM. Chain will return error messages.")
            
            # Return a fallback function that just returns error messages
            def fallback_chain(inputs: dict) -> dict:
                return {output_key: f"ERROR: No LLM available. Agent {self.name} cannot process this request."}
            
            return fallback_chain
        
        prompt = PromptTemplate.from_template(prompt_template)
        
        # Create a runnable sequence
        chain = prompt | self.llm
        
        # Create a wrapper function to mimic the old invoke behavior
        def invoke_wrapper(inputs: dict) -> dict:
            try:
                print(f"Running {self.name} chain with model {self.model_name}...")
                result = chain.invoke(inputs)
                if hasattr(result, 'content'):
                    return {output_key: result.content}
                elif isinstance(result, dict) and 'content' in result:
                    return {output_key: result['content']}
                elif isinstance(result, str):
                    return {output_key: result}
                else:
                    return {output_key: str(result)}
            except Exception as e:
                print(f"Error in chain execution: {str(e)}")
                traceback.print_exc()
                # Return a fallback response
                return {output_key: f"Error occurred: {str(e)}"}
            
        return invoke_wrapper
    
    def add_to_memory(self, data: Any) -> None:
        """
        Add data to the agent's memory.
        
        Args:
            data: The data to add to memory
        """
        self.memory.append(data)
    
    def clear_memory(self) -> None:
        """Clear the agent's memory."""
        self.memory = []
    
    def run(self, **kwargs) -> Dict[str, Any]:
        """
        Run the agent. This must be implemented by all subclasses.
        
        Returns:
            A dictionary containing the agent's output
        """
        raise NotImplementedError("Subclasses must implement the run method")