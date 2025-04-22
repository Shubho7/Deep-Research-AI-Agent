"""
Research agent that searches for information using Tavily.
"""
from typing import Dict, List, Any, Optional
import traceback
from agents.base_agent import BaseAgent
from utils.tavily_client import TavilySearchClient
from utils.config import RESEARCH_MODEL, MAX_SEARCH_DEPTH, MAX_SEARCH_RESULTS

class ResearchAgent(BaseAgent):
    """
    Agent responsible for performing research using Tavily.
    """
    
    def __init__(
        self,
        name: str = "Research Agent",
        description: str = "Searches for information using Tavily",
        model_name: str = RESEARCH_MODEL,
        api_key: Optional[str] = None,
        temperature: float = 0.0,
    ):
        """
        Initialize the research agent.
        
        Args:
            name: The name of the agent
            description: A short description of the agent's purpose
            model_name: The name of the LLM model to use
            api_key: The OpenAI API key
            temperature: The temperature setting for the LLM
        """
        print(f"Initializing {name} with {model_name}")
        super().__init__(name, description, model_name, api_key, temperature)
        self.tavily_client = TavilySearchClient()
        
        # Create the query generation chain
        print("Creating query generation chain...")
        self.query_gen_chain = self.create_chain(
            """
            You are a research assistant tasked with generating effective search queries.
            Based on the research topic provided, generate {num_queries} specific search queries
            that will help gather comprehensive information on the topic.
            
            Research topic: {research_topic}
            
            Output {num_queries} search queries, one per line, that are specific, clear, and focused
            on different aspects of the research topic.
            """,
            output_key="search_queries"
        )
        
        # Create the information synthesis chain
        print("Creating information synthesis chain...")
        self.synthesis_chain = self.create_chain(
            """
            You are a research assistant tasked with synthesizing information from multiple sources.
            
            Research topic: {research_topic}
            
            Below are the search results from multiple queries:
            
            {search_results}
            
            Based on these results, provide a comprehensive synthesis of the information.
            Focus on extracting key facts, concepts, and insights relevant to the research topic.
            Organize the information in a structured way that highlights the most important points.
            Cite sources where appropriate using [Source: URL] notation.
            
            Your synthesis should be thorough, accurate, and well-organized.
            """,
            output_key="synthesis"
        )
        print(f"{name} initialization complete.")
    
    def generate_search_queries(self, research_topic: str, num_queries: int = 3) -> List[str]:
        """
        Generate search queries for the research topic.
        
        Args:
            research_topic: The research topic to generate queries for
            num_queries: The number of queries to generate
            
        Returns:
            A list of search queries
        """
        print(f"Generating {num_queries} search queries for topic: '{research_topic}'")
        try:
            # The chain is now a callable function, not an object with invoke()
            result = self.query_gen_chain({
                "research_topic": research_topic,
                "num_queries": num_queries
            })
            
            # Split the output into a list of queries
            queries = result["search_queries"].strip().split("\n")
            
            # Clean up the queries (remove numbers, etc.)
            clean_queries = []
            for query in queries:
                # Remove potential numbering or prefixes
                if "." in query:
                    parts = query.split(".", 1)
                    if parts[0].strip().isdigit():
                        query = parts[1].strip()
                clean_queries.append(query.strip())
            
            print(f"Generated queries: {clean_queries}")
            return clean_queries
        except Exception as e:
            print(f"Error generating search queries: {e}")
            traceback.print_exc()
            return [research_topic]  # Fallback to using the topic itself
    
    def search(self, query: str, search_depth: str = "basic") -> Dict[str, Any]:
        """
        Perform a search using the Tavily API.
        
        Args:
            query: The search query
            search_depth: Either "basic" or "advanced" for more comprehensive search
            
        Returns:
            The search results
        """
        return self.tavily_client.search(
            query=query,
            max_results=MAX_SEARCH_RESULTS,
            search_depth=search_depth
        )
    
    def format_search_results(self, results_list: List[Dict[str, Any]]) -> str:
        """
        Format search results for the synthesis chain.
        
        Args:
            results_list: A list of dictionaries containing results from multiple searches
            
        Returns:
            A formatted string of search results
        """
        print(f"Formatting search results from {len(results_list)} queries")
        formatted_results = ""
        
        for i, results in enumerate(results_list):
            query = results.get("query", f"Query {i+1}")
            formatted_results += f"\n## RESULTS FOR: {query}\n\n"
            
            if "results" not in results or not results["results"]:
                formatted_results += "No results found for this query.\n\n"
                continue
            
            for j, result in enumerate(results["results"]):
                formatted_results += f"### Result {j+1}: {result.get('title', 'No title')}\n"
                formatted_results += f"URL: {result.get('url', 'No URL')}\n"
                formatted_results += f"Content: {result.get('content', 'No content available')}\n\n"
        
        # Log a short preview
        preview_length = min(500, len(formatted_results))
        print(f"Formatted results (preview): {formatted_results[:preview_length]}...")
        return formatted_results
    
    def run(self, research_topic: str, num_queries: int = 3, search_depth: str = "basic") -> Dict[str, Any]:
        """
        Run the research agent on the given topic.
        
        Args:
            research_topic: The research topic to search for
            num_queries: The number of search queries to generate
            search_depth: The depth of the search ("basic" or "advanced")
            
        Returns:
            A dictionary containing the research results
        """
        print(f"\n=== Starting research on topic: '{research_topic}' ===")
        try:
            # Generate search queries
            print("Step 1: Generating search queries...")
            queries = self.generate_search_queries(research_topic, num_queries)
            
            # Perform searches for each query
            print("Step 2: Performing searches for each query...")
            search_results = []
            for i, query in enumerate(queries):
                print(f"  Searching for query {i+1}/{len(queries)}: '{query}'")
                results = self.search(query, search_depth)
                results["query"] = query  # Add the query to the results
                search_results.append(results)
                self.add_to_memory(results)
            
            # Format the search results for synthesis
            print("Step 3: Formatting search results...")
            formatted_results = self.format_search_results(search_results)
            
            # Synthesize the information
            print("Step 4: Synthesizing information...")
            # The chain is now a callable function, not an object with invoke()
            synthesis = self.synthesis_chain({
                "research_topic": research_topic,
                "search_results": formatted_results
            })
            
            print("Research completed successfully.")
            return {
                "research_topic": research_topic,
                "queries": queries,
                "search_results": search_results,
                "synthesis": synthesis["synthesis"]
            }
        except Exception as e:
            print(f"Error in research agent: {e}")
            traceback.print_exc()
            return {
                "research_topic": research_topic,
                "queries": [],
                "search_results": [],
                "synthesis": f"An error occurred during research: {str(e)}",
                "error": str(e)
            } 