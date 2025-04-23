"""
Configuration utilities for the DeepResearchAI system.
"""
import os
from dotenv import load_dotenv

load_dotenv()

# API Keys
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")

# Model Configuration
DEFAULT_MODEL = "gemini-2.0-flash"
RESEARCH_MODEL = "gemini-2.0-flash"
DRAFTING_MODEL = "gemini-1.5-flash"
FACT_CHECK_MODEL = "gemini-2.0-flash"  
CITATION_MODEL = "gemini-1.5-flash"   

# Alternate models to fall back to if primary models fail
FALLBACK_MODELS = ["gemini-1.5-flash", "gemini-2.0-flash", "gemini-2.5-flash"]

# Research Configuration
MAX_SEARCH_RESULTS = 20
MAX_SEARCH_DEPTH = 3
SEARCH_TIMEOUT = 60 

# Fact-Checking Configuration
ENABLE_FACT_CHECK_BY_DEFAULT = True
FACT_CHECK_CONFIDENCE_THRESHOLD = 0.8  # Minimum confidence level to accept a fact

# Citation Configuration
ENABLE_CITATIONS_BY_DEFAULT = True
DEFAULT_CITATION_STYLE = "APA"  # Default citation style

# Define a function to validate configuration
def validate_config():
    """Validate that all required configuration variables are set."""
    required_vars = ["GOOGLE_API_KEY", "TAVILY_API_KEY"]
    missing_vars = [var for var in required_vars if not globals().get(var)]
    
    if missing_vars:
        raise EnvironmentError(
            f"Missing required environment variables: {', '.join(missing_vars)}. "
            f"Please set these in your .env file."
        )
    
    return True 