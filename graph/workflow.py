from typing import Dict, List, Any, Annotated, TypedDict, Literal
from enum import Enum
import json
from langgraph.graph import StateGraph, END
from agents.research_agent import ResearchAgent
from agents.drafting_agent import DraftingAgent
from agents.fact_checking_agent import FactCheckingAgent
from agents.citation_agent import CitationAgent

# Global variable to store the latest research result
# This is a workaround for state handling issues in the LangGraph execution
_latest_research_result = None

# Define state types
class NodeNames(str, Enum):
    RESEARCH = "research_node"  
    DRAFT = "draft_node"   
    FACT_CHECK = "fact_check_node"  
    CITATION = "citation_node"   
    IMPROVE = "improve_node"    

class ResearchState(TypedDict):
    """State for the research workflow."""
    research_topic: str
    research_depth: str
    num_queries: int
    research_results: Dict[str, Any]
    draft_result: Dict[str, Any] 
    fact_check_result: Dict[str, Any]  
    citation_result: Dict[str, Any] 
    final_answer: str
    status: Literal["research", "draft", "fact_check", "citation", "improve", "complete", "error"]
    error: str

def create_research_workflow() -> StateGraph:
    """
    Create a workflow graph for the research process.
    
    Returns:
        StateGraph: The research workflow graph
    """
    # Create the agents
    research_agent = ResearchAgent()
    drafting_agent = DraftingAgent()
    fact_checking_agent = FactCheckingAgent() 
    citation_agent = CitationAgent()  
    
    # Create the graph
    workflow = StateGraph(ResearchState)
    
    # Define the nodes
    def research(state: ResearchState) -> ResearchState:
        """Run the research agent to gather information."""
        try:
            research_results = research_agent.run(
                research_topic=state["research_topic"],
                num_queries=state["num_queries"],
                search_depth=state["research_depth"]
            )
            return {
                **state,
                "research_results": research_results,
                "status": "draft"
            }
        except Exception as e:
            return {
                **state,
                "status": "error",
                "error": f"Research error: {str(e)}"
            }
    
    def draft(state: ResearchState) -> ResearchState:
        """Run the drafting agent to create an initial draft."""
        try:
            # Get the research synthesis from the research results
            research_synthesis = state["research_results"]["synthesis"]
            
            # Run the drafting agent
            draft_results = drafting_agent.run(
                research_topic=state["research_topic"],
                research_synthesis=research_synthesis,
                improve=False 
            )
            
            return {
                **state,
                "draft_result": draft_results,
                "status": "fact_check"  
            }
        except Exception as e:
            return {
                **state,
                "status": "error",
                "error": f"Drafting error: {str(e)}"
            }
    
    def fact_check(state: ResearchState) -> ResearchState:
        """Run the fact-checking agent to verify information accuracy."""
        try:
            # Get the research synthesis and initial draft
            research_synthesis = state["research_results"]["synthesis"]
            initial_draft = state["draft_result"]["initial_draft"]
            
            # Run the fact-checking agent
            fact_check_results = fact_checking_agent.run(
                research_topic=state["research_topic"],
                research_synthesis=research_synthesis,
                draft=initial_draft
            )
            
            return {
                **state,
                "fact_check_result": fact_check_results,
                "status": "citation"
            }
        except Exception as e:
            return {
                **state,
                "status": "error",
                "error": f"Fact-checking error: {str(e)}"
            }
    
    def citation(state: ResearchState) -> ResearchState:
        """Run the citation agent to format and validate sources."""
        try:
            # Get the research synthesis and fact-checked draft
            research_synthesis = state["research_results"]["synthesis"]
            
            # Use the corrected draft from fact-checking if available, otherwise use the initial draft
            if "fact_check_result" in state and "corrected_draft" in state["fact_check_result"]:
                draft_to_process = state["fact_check_result"]["corrected_draft"]
            else:
                draft_to_process = state["draft_result"]["initial_draft"]
            
            # Run the citation agent
            citation_results = citation_agent.run(
                research_topic=state["research_topic"],
                research_synthesis=research_synthesis,
                draft=draft_to_process
            )
            
            return {
                **state,
                "citation_result": citation_results,
                "status": "improve"
            }
        except Exception as e:
            return {
                **state,
                "status": "error",
                "error": f"Citation error: {str(e)}"
            }
    
    def improve(state: ResearchState) -> ResearchState:
        """Run the drafting agent to improve the final draft."""
        try:
            # Use the final draft from citation agent if available, otherwise use the corrected draft or initial draft
            if "citation_result" in state and "final_draft" in state["citation_result"]:
                draft_to_improve = state["citation_result"]["final_draft"]
            elif "fact_check_result" in state and "corrected_draft" in state["fact_check_result"]:
                draft_to_improve = state["fact_check_result"]["corrected_draft"]
            else:
                draft_to_improve = state["draft_result"]["initial_draft"]
            
            # Improve the draft
            improved_draft = drafting_agent.improve_answer(
                research_topic=state["research_topic"],
                draft=draft_to_improve
            )
            
            # Ensure the status is set to complete
            result_state = {
                **state,
                "final_answer": improved_draft,
                "status": "complete"
            }
            
            # Printing useful debug info
            print(f"IMPROVE NODE: Setting final state to complete")
            print(f"IMPROVE NODE: Final answer preview: {improved_draft[:50]}...")
            print(f"IMPROVE NODE: Status is set to: {result_state['status']}")
            
            # Store the result directly in global state for the parent function to use
            global _latest_research_result
            _latest_research_result = {
                "research_topic": state["research_topic"],
                "status": "complete",
                "research_results": state.get("research_results", {}),
                "final_answer": improved_draft
            }
            
            return result_state
        except Exception as e:
            print(f"Error in improve step: {str(e)}")
            return {
                **state,
                "status": "error",
                "error": f"Improvement error: {str(e)}"
            }
    
    # Add nodes to the graph - use string values instead of enum members
    workflow.add_node(NodeNames.RESEARCH.value, research)
    workflow.add_node(NodeNames.DRAFT.value, draft)
    workflow.add_node(NodeNames.FACT_CHECK.value, fact_check) 
    workflow.add_node(NodeNames.CITATION.value, citation) 
    workflow.add_node(NodeNames.IMPROVE.value, improve)
    
    # Define the edges - use string values and update the flow
    workflow.add_edge(NodeNames.RESEARCH.value, NodeNames.DRAFT.value)
    workflow.add_edge(NodeNames.DRAFT.value, NodeNames.FACT_CHECK.value)  
    workflow.add_edge(NodeNames.FACT_CHECK.value, NodeNames.CITATION.value)  
    workflow.add_edge(NodeNames.CITATION.value, NodeNames.IMPROVE.value)  
    workflow.add_edge(NodeNames.IMPROVE.value, END)
    
    # Define conditional edges for error handling
    def route_after_research(state: ResearchState) -> str:
        if state["status"] == "error":
            return END
        return NodeNames.DRAFT.value
    
    def route_after_draft(state: ResearchState) -> str:
        if state["status"] == "error":
            return END
        return NodeNames.FACT_CHECK.value  
    
    def route_after_fact_check(state: ResearchState) -> str:
        if state["status"] == "error":
            return END
        return NodeNames.CITATION.value
    
    def route_after_citation(state: ResearchState) -> str:
        if state["status"] == "error":
            return END
        return NodeNames.IMPROVE.value
    
    def route_after_improve(state: ResearchState) -> str:
        return END
    
    # Add conditional edges - use string values
    workflow.add_conditional_edges(
        NodeNames.RESEARCH.value,
        route_after_research
    )
    
    workflow.add_conditional_edges(
        NodeNames.DRAFT.value,
        route_after_draft
    )
    
    workflow.add_conditional_edges(
        NodeNames.FACT_CHECK.value,
        route_after_fact_check
    )
    
    workflow.add_conditional_edges(
        NodeNames.CITATION.value,
        route_after_citation
    )
    
    workflow.add_conditional_edges(
        NodeNames.IMPROVE.value,
        route_after_improve
    )
    
    # Set the entry point - use string value
    workflow.set_entry_point(NodeNames.RESEARCH.value)
    
    return workflow

def extract_values_from_state(state):
    """
    Extract values from a state object, handling different formats.
    
    Args:
        state: The state object from LangGraph
        
    Returns:
        A dictionary of extracted values
    """
    
    if isinstance(state, dict):
        # If it's just a dict, check if it contains values
        if "values" in state:
            return state["values"]
        # If it contains __metadata__ and other keys, it might be a direct state
        if "__metadata__" in state:
            # Create a copy without the metadata
            return {k: v for k, v in state.items() if k != "__metadata__"}
        # Otherwise return as is
        return state
    # If it has a values attribute (sometimes the case in newer versions)
    elif hasattr(state, "values"):
        return state.values
    # Otherwise try to convert to dict
    else:
        try:
            return dict(state)
        except:
            # Access common attributes
            result = {}
            for attr in ["research_topic", "research_depth", "num_queries", 
                        "research_results", "draft_result", "final_answer", 
                        "status", "error"]:
                if hasattr(state, attr):
                    result[attr] = getattr(state, attr)
            return result

def run_research_workflow(
    research_topic: str,
    research_depth: str = "basic",
    num_queries: int = 3,
    skip_fact_check: bool = False,  # Parameter kept for backward compatibility but will be ignored
    skip_citations: bool = False  # Parameter kept for backward compatibility but will be ignored
) -> Dict[str, Any]:
    """
    Run the research workflow on a given topic.
    
    Args:
        research_topic: The topic to research
        research_depth: The depth of research ("basic" or "advanced")
        num_queries: The number of search queries to generate
        skip_fact_check: DEPRECATED - Fact-checking is now always included for accuracy
        skip_citations: DEPRECATED - Citations are now always included for proper source attribution
        
    Returns:
        A dictionary containing the research results, draft, and final answer
    """
    # Reset the global result variable
    global _latest_research_result
    _latest_research_result = None
    
    # Create the workflow
    workflow = create_research_workflow()
    
    # Create the graph compiler
    graph = workflow.compile()
    
    # Create the initial state
    initial_state: ResearchState = {
        "research_topic": research_topic,
        "research_depth": research_depth,
        "num_queries": num_queries,
        "research_results": {},
        "draft_result": {}, 
        "fact_check_result": {}, 
        "citation_result": {}, 
        "final_answer": "",
        "status": "research",
        "error": ""
    }
    
    # Forcing both fact-checking and citations to be always included
    skip_fact_check = False
    skip_citations = False
    
    # Variables to track the state at each step
    final_state_raw = None
    complete_state = None
    last_node_state = {
        "research": None,
        "draft": None,
        "fact_check": None,
        "citation": None,
        "improve": None
    }
    last_node_name = None
    
    # Variable to collect any final answer text during the process
    final_answer_text = ""
    
    # Run the graph
    try:
        for state in graph.stream(initial_state):
            print("STATE EVENT: ", end="")
            
            final_state_raw = state  # Keep track of the last state
            
            # Extract the actual state values
            current_state = extract_values_from_state(state)
            
            # Check if we have a final answer in the current state
            if "final_answer" in current_state and current_state["final_answer"]:
                # Always save any final answer we find
                final_answer_text = current_state["final_answer"]
                print(f"Found final answer! First 30 chars: {final_answer_text[:30]}...")
            
            # Log metadata if available
            if isinstance(state, dict) and "__metadata__" in state:
                metadata = state["__metadata__"]
                event_type = metadata.get("event_type", "")
                node_name = metadata.get("node_name", "")
                
                print(f"{event_type} - {node_name}")
                
                # Track the node we're processing
                if event_type == "enter":
                    print(f"Starting {node_name}...")
                    last_node_name = node_name
                elif event_type == "exit":
                    print(f"Completed {node_name}.")
                    
                    # Store the node's output state
                    if node_name == "research_node":
                        last_node_state["research"] = current_state
                    elif node_name == "draft_node":
                        last_node_state["draft"] = current_state
                    elif node_name == "improve_node":
                        last_node_state["improve"] = current_state
                        
                        # If we just completed the improve node and it has a final answer,
                        # This is the most important state - the actual result of our research!
                        if "final_answer" in current_state:
                            print(f"Captured final answer from improve node")
                            complete_state = {
                                **current_state,
                                "status": "complete"
                            }
            else:
                print("state event without metadata")
                        
            # Check for errors only
            if "status" in current_state and current_state["status"] == "error":
                print(f"Error: {current_state.get('error', 'Unknown error')}")
                break
    except Exception as e:
        print(f"Error during workflow execution: {str(e)}")
        return {
            "research_topic": research_topic,
            "status": "error",
            "error": f"Workflow execution error: {str(e)}"
        }
    
    # Check if we have a direct result from the improve node (via global variable)
    if _latest_research_result is not None:
        print("Using direct result from improve node (global variable)")
        return _latest_research_result
    
    # First check: If we have a complete state, use that
    if complete_state and "final_answer" in complete_state and complete_state["final_answer"]:
        print("Using captured complete state")
        return {
            "research_topic": research_topic,
            "status": "complete",
            "research_results": complete_state.get("research_results", {}),
            "final_answer": complete_state["final_answer"]
        }
    
    # Second check: If we have a final answer text from somewhere, use that
    if final_answer_text:
        print("Using captured final answer text")
        return {
            "research_topic": research_topic,
            "status": "complete",
            "final_answer": final_answer_text,
            "research_results": last_node_state.get("research", {}).get("research_results", {})
        }
    
    # Third check: If we have the improve node's state with a final answer
    if last_node_state["improve"] and "final_answer" in last_node_state["improve"]:
        print("Using improve node state")
        return {
            "research_topic": research_topic,
            "status": "complete",
            "research_results": last_node_state["improve"].get("research_results", {}),
            "final_answer": last_node_state["improve"]["final_answer"]
        }
    
    # If we don't have a final state, return an error
    if final_state_raw is None:
        return {
            "research_topic": research_topic,
            "status": "error",
            "error": "No final state was produced by the workflow."
        }
    
    # Extract the final state values
    final_state = extract_values_from_state(final_state_raw)
    
    # Last check: check if the final state has a final answer
    if "final_answer" in final_state and final_state["final_answer"]:
        print("Using final state")
        return {
            "research_topic": research_topic,
            "status": "complete",
            "research_results": final_state.get("research_results", {}),
            "final_answer": final_state["final_answer"]
        }
    
    # Final fallback: Standard output structure
    result = {
        "research_topic": research_topic,
        "status": final_state.get("status", "error")
    }
    
    # Include research_results if available
    if "research_results" in final_state:
        result["research_results"] = final_state["research_results"]
    
    # Include error if status is error
    if result["status"] == "error" and "error" in final_state:
        result["error"] = final_state["error"]
    else:
        # If we got here without finding a complete state but also no explicit error,
        # it's likely something went wrong but we're missing the error info
        result["status"] = "error"
        result["error"] = "Research completed but no final answer was produced."
    
    return result 