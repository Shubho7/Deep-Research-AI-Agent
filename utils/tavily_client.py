"""
Tavily API client wrapper for the DeepResearchAI system.
"""
from typing import Dict, List, Optional, Any
import json
import traceback
from tavily import TavilyClient
from utils.config import TAVILY_API_KEY, MAX_SEARCH_RESULTS

class TavilySearchClient:
    """
    A wrapper around the Tavily API client for performing web searches.
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the Tavily search client.
        
        Args:
            api_key: Optional Tavily API key. If not provided, will use the one from config.
        """
        self.api_key = api_key or TAVILY_API_KEY
        if not self.api_key:
            print("WARNING: No Tavily API key provided. Searches will fail.")
        try:
            print(f"Initializing Tavily client...")
            self.client = TavilyClient(api_key=self.api_key)
            print("Tavily client initialized successfully.")
        except Exception as e:
            print(f"Error initializing Tavily client: {e}")
            traceback.print_exc()
            self.client = None
    
    def search(
        self, 
        query: str, 
        max_results: int = MAX_SEARCH_RESULTS,
        search_depth: str = "basic",
        include_domains: Optional[List[str]] = None,
        exclude_domains: Optional[List[str]] = None,
        include_answer: bool = True,
        include_raw_content: bool = False
    ) -> Dict[str, Any]:
        """
        Perform a search using the Tavily API.
        
        Args:
            query: The search query
            max_results: Maximum number of results to return
            search_depth: Either "basic" or "advanced" for more comprehensive search
            include_domains: List of domains to include in the search
            exclude_domains: List of domains to exclude from the search
            include_answer: Whether to include an AI-generated answer
            include_raw_content: Whether to include the raw content of the pages
            
        Returns:
            A dictionary containing the search results
        """
        if self.client is None:
            print("Tavily client is not initialized. Cannot perform search.")
            return {
                "query": query,
                "results": [],
                "answer": "Error: Tavily client is not initialized."
            }
            
        print(f"Searching with Tavily for: '{query}'")
        print(f"  - Max results: {max_results}")
        print(f"  - Search depth: {search_depth}")
        
        try:
            print("Calling Tavily API...")
            response = self.client.search(
                query=query,
                max_results=max_results,
                search_depth=search_depth,
                include_domains=include_domains,
                exclude_domains=exclude_domains,
                include_answer=include_answer,
                include_raw_content=include_raw_content
            )
            
            # Log basic information about the results
            result_count = len(response.get("results", []))
            print(f"Tavily search complete. Got {result_count} results.")
            
            return response
        except Exception as e:
            print(f"Error performing Tavily search: {e}")
            traceback.print_exc()
            return {
                "query": query,
                "results": [],
                "answer": f"Error performing search: {str(e)}",
            }
    
    def extract_results(self, search_results: Dict[str, Any]) -> List[Dict[str, str]]:
        """
        Extract the relevant information from the search results.
        
        Args:
            search_results: The raw search results from Tavily
            
        Returns:
            A list of dictionaries containing the structured information
        """
        structured_results = []
        
        if "results" not in search_results:
            print("No 'results' key found in search results.")
            return structured_results
        
        for result in search_results["results"]:
            structured_results.append({
                "title": result.get("title", "No title"),
                "url": result.get("url", ""),
                "content": result.get("content", "No content available"),
                "score": result.get("score", 0),
            })
        
        return structured_results 