# DeepResearchAI

A deep research AI agentic system built using LangChain, LangGraph, and Tavily.

## Overview

DeepResearchAI leverages Google's Gemini LLM models (gemini-1.5-flash & gemini-2.0-flash) to perform comprehensive research on any topic. The system integrates web search capabilities through the Tavily API to gather information and then uses Gemini to synthesize the findings into a coherent research document. The architecture is built on LangChain's component framework and LangGraph's state management system to create a robust, agentic research workflow.

## Features

- **AI-powered research**: Utilizes Google Gemini LLM models for generating search queries and synthesizing information
- **Web search integration**: Uses Tavily API to search the web for up-to-date information
- **Customizable research depth**: Choose between basic and advanced research depths
- **User-friendly interface**: Easy-to-use Streamlit UI for interacting with the system
- **Markdown output**: Research is provided in Markdown format, easy to use in documentation
- **Advanced LangChain integration**: Leverages LangChain's components for prompt management, memory, and callbacks
- **LangGraph workflow**: Implements a sophisticated state machine for research orchestration

## Prerequisites

- Python 3.8+
- Google API key (for Gemini access)
- Tavily API key (for web search)

## Installation

1. Clone this repository:
```bash
git clone https://github.com/yourusername/Deep-Research-AI-Agent.git
cd Deep-Research-AI-Agent
```

2. Install the required dependencies:
```bash
pip install -r requirements.txt
```

3. Create a `.env` file in the root directory with your API keys:
```
GOOGLE_API_KEY=your_google_api_key_here
TAVILY_API_KEY=your_tavily_api_key_here
```

## Usage

### Using the Command Line Interface

```bash
python main.py --topic "Your research topic" --depth basic --queries 3
```

Optional arguments:
- `--topic`: The research topic (required)
- `--depth`: Research depth (basic or advanced, default: basic)
- `--queries`: Number of search queries to generate (default: 3)
- `--output`: Output file path for the research results in JSON format

## How It Works

DeepResearchAI implements a sophisticated dual-agent architecture orchestrated through LangGraph and LangChain frameworks:

### Agent Architecture

1. **Research Agent**: Responsible for information gathering and synthesis
   - Implements a LangChain `RunnableAgent` with Gemini 1.5 Pro (context window: 1M tokens)
   - Uses structured output parsing with Pydantic models for consistent data handling
   - Generates optimized search queries using few-shot learning techniques
   - Executes web searches via Tavily API to crawl relevant websites
   - Synthesizes information from multiple sources using advanced retrieval techniques
   - Implements fallback mechanisms with automatic retry logic for model reliability
   - Uses token counting to optimize context window usage

2. **Drafting Agent**: Transforms research into structured content
   - Implements a LangChain `RunnableAgent` with Gemini 1.0 Pro (temperature: 0.2 for factual content)
   - Creates initial drafts based on synthesized research using structured templates
   - Uses `ConversationSummaryMemory` to maintain context across drafting iterations
   - Improves content quality through a dedicated review process with custom evaluation metrics
   - Ensures proper citation and attribution of sources using metadata tracking
   - Formats output in markdown with customizable templates
   - Implements content filtering for factual accuracy and relevance

### Workflow Orchestration

The system uses LangGraph to create a directed workflow with the following stages:

1. **Query Generation**: The Research Agent generates targeted search queries based on the research topic
2. **Web Search & Crawling**: Executes the generated queries using Tavily API to gather information from across the web
3. **Information Synthesis**: The Research Agent consolidates and synthesizes the search results
4. **Initial Drafting**: The Drafting Agent creates a structured first draft of the research document
5. **Review & Improvement**: The Drafting Agent refines the draft for better quality and readability

This workflow is managed by a StateGraph that tracks the research process and handles transitions between different stages, ensuring a comprehensive research outcome.

## Project Structure

- `main.py`: Command-line interface for running research workflows
- `agents/`: Contains the agent implementations
  - `base_agent.py`: Abstract base class defining common agent functionality
  - `research_agent.py`: Implementation of the Research Agent for information gathering
  - `drafting_agent.py`: Implementation of the Drafting Agent for content creation
- `graph/`: Contains the workflow orchestration
  - `workflow.py`: LangGraph implementation of the research workflow
- `utils/`: Utility functions and configuration
  - `config.py`: System configuration and environment variables
  - `tavily_client.py`: Client wrapper for the Tavily search API

## Implementation Details

### LangChain Integration

The system leverages LangChain's comprehensive framework for LLM application development:

- **Model Integration**: Uses `ChatGoogleGenerativeAI` to interface with Google's Gemini models:
  - Gemini 1.0 Pro for standard research tasks and query generation
  - Gemini 1.5 Pro for advanced synthesis and long-context understanding
  - Configurable temperature and top_p parameters for controlling output creativity

- **Prompt Engineering**: Implements sophisticated prompt management:
  - Uses `ChatPromptTemplate` and `MessagesPlaceholder` for structured conversations
  - Implements few-shot learning with carefully crafted examples
  - Utilizes system messages to define agent roles and constraints

- **Chain Construction**:
  - Creates `SequentialChain` objects for multi-step reasoning processes
  - Implements `RunnablePassthrough` for efficient data handling between chain steps
  - Uses `RunnableLambda` for custom data transformations

- **Memory Systems**:
  - Implements `ConversationBufferMemory` for maintaining context across interactions
  - Uses `ConversationSummaryMemory` for long research sessions
  - Leverages token-based memory management to stay within model context limits

- **Callbacks & Observability**:
  - Implements custom callback handlers for logging and debugging
  - Uses tracing for performance monitoring and optimization
  - Provides detailed metrics on token usage and latency

### LangGraph Workflow

The research process is implemented as a directed graph using LangGraph's state management system:

- **StateGraph Architecture**:
  - Implements a `StateGraph` with typed nodes for each research phase
  - Uses `RunnableBranch` for conditional logic between workflow stages
  - Maintains a persistent state object that tracks the entire research process
  - Implements checkpointing for reliability and resumability

- **State Transitions**:
  - Defines explicit transitions between research, drafting, and improvement phases
  - Uses conditional edges based on quality assessments and completion criteria
  - Implements fallback paths for handling model limitations or API failures
  - Provides cycle detection to prevent infinite loops in the research process

- **Event-Driven Processing**:
  - Implements event listeners for monitoring state changes
  - Uses event handlers for logging and debugging
  - Provides real-time feedback on research progress

- **Parallel Processing**:
  - Implements parallel execution for independent research tasks
  - Uses thread management for concurrent API calls
  - Optimizes resource utilization during information gathering phases

### Tavily Integration

The system uses Tavily's API for web crawling and information retrieval, tightly integrated with the LangChain ecosystem:

- **Search Configuration**:
  - Configurable search depth (basic or advanced)
  - Customizable result limits and domain filtering
  - Support for both general search and specific answer extraction
  - Implements content filtering and NSFW protection

- **LangChain Tool Integration**:
  - Implements Tavily as a LangChain Tool for agent usage
  - Uses structured output parsing for consistent data handling
  - Integrates with LangChain's caching system for efficient resource usage

- **Error Handling**:
  - Implements exponential backoff for rate limiting
  - Uses circuit breakers for API reliability
  - Provides fallback mechanisms for search failures
  - Maintains detailed logging for troubleshooting

## Acknowledgments

- Google Gemini for providing the LLM models
- Tavily API for web search capabilities and website crawling
- LangChain for LLM integration and chain-of-thought processing
- LangGraph for workflow orchestration and state management