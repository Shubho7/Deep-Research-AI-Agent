# DeepResearchAI

A deep research AI agentic system built using LangChain, LangGraph, and Tavily.

## Overview

DeepResearchAI leverages Google's Gemini LLM models like `gemini-2.0-flash`, `gemini-1.5-flash` & `gemini-1.5-pro` to perform comprehensive research on any topic. It integrates web search through the Tavily API, synthesizes findings, drafts content, fact-checks accuracy, formats citations, and exports results to PDF.

The architecture uses:
- **LangChain** for prompt management, LLM integration, and chain creation
- **LangGraph** for workflow orchestration and state management
- **Tavily** for web search and website crawling

## Features

- **AI-powered research**: Utilizes Google Gemini LLM models for generating search queries and synthesizing information
- **Web search integration**: Uses Tavily API to search the web for up-to-date information
- **Customizable research depth**: Choose between basic and advanced research depths
- **Markdown output**: Research is provided in Markdown format, easy to use in documentation
- **PDF export**: Ability to save research results as professionally formatted PDF documents
- **LangChain integration**: Uses LangChain's components for prompt management and chain creation
- **LangGraph workflow**: Implements a state machine for research orchestration

## Prerequisites

- Python 3.8+
- Google API key (for Gemini access)
- Tavily API key (for web search)

## Installation

1. Clone the repository:
    ```bash
    git clone https://github.com/yourusername/Deep-Research-AI-Agent.git
    cd Deep-Research-AI-Agent
    ```
2. Install dependencies:
    ```bash
    pip install -r requirements.txt
    ```
3. Set environment variables in a `.env` file:
    ```dotenv
    GOOGLE_API_KEY=your_google_api_key
    TAVILY_API_KEY=your_tavily_api_key
    ```

## Project Structure

```
Deep-Research-AI-Agent/
├── main.py               
├── README.md             
├── requirements.txt      
├── agents/                           # Agent implementations
│   ├── base_agent.py                 # Abstract BaseAgent
│   ├── research_agent.py             # ResearchAgent
│   ├── drafting_agent.py             # DraftingAgent
│   ├── fact_checking_agent.py        # FactCheckingAgent
│   ├── citation_agent.py             # CitationAgent
│   └── __init__.py
├── graph/                            # Workflow orchestration
│   ├── workflow.py                   # LangGraph state machine
│   └── __init__.py
└── utils/                            # Utility modules
    ├── config.py                     # Configuration loader & constants
    ├── tavily_client.py              # Tavily API wrapper
    ├── pdf_export.py                 # PDF export functionality
    └── __init__.py
```

## Usage

```bash
python main.py --topic "Your topic" --depth basic --queries 3
```
- `--topic` (required)
- `--depth` (basic|advanced, default: basic)
- `--queries` (default: 3)
- Fact-checking and citation agents are always enabled

After research completion, you'll be asked if you want to save the results as a PDF document.


## Agent Architecture

DeepResearchAI implements a multi-agent architecture orchestrated through LangGraph:

1. **Research Agent (`agents/research_agent.py`)**: Responsible for information gathering and synthesis
   - Inherits from the `BaseAgent` class
   - Uses `query_gen_chain` to generate search queries based on the research topic
   - Executes web searches via Tavily API to gather information
   - Formats search results into a structured markdown format
   - Uses `synthesis_chain` to consolidate information and include source citations using [Source: URL] notation
   - Returns a dictionary with the research topic, queries, search results, and synthesis

2. **Drafting Agent (`agents/drafting_agent.py`)**: Transforms research into structured content
   - Inherits from the `BaseAgent` class
   - Uses `drafting_chain` to create initial drafts based on the research synthesis
   - Uses `improve_chain` to refine and enhance the document quality
   - Has simple memory storage via the `add_to_memory` method inherited from BaseAgent
   - Returns a dictionary with the initial draft and optionally an improved draft

3. **Fact-Checking Agent (`agents/fact_checking_agent.py`)**: Verifies and corrects factual accuracy in drafts
   - Uses a `fact_checking_chain` to identify inaccuracies, unsupported claims, and misrepresentations
   - Produces a detailed `fact_check_report` describing each issue
   - Uses a `correction_chain` to apply corrections and maintain document flow
   - Returns a dictionary containing the fact check report and corrected draft

4. **Citation Agent (`agents/citation_agent.py`)**: Extracts, formats, and validates all citations in the document
   - Uses an `extraction_chain` to identify existing citations and flag uncited claims
   - Formats citations to APA style via a `formatting_chain`, adding an auto-generated References section
   - Validates citations with a `validation_chain` and attempts to split the result into a report and document
   - Returns a dictionary with citation analysis, formatted draft, validation report, and final draft

## LangGraph Workflow Orchestration (`graph/workflow.py`)

The system uses LangGraph's StateGraph to create a directed workflow with the following nodes:

1. **research_node**: Uses ResearchAgent to generate queries, perform searches, and synthesize information
2. **draft_node**: Uses DraftingAgent to create an initial draft based on the synthesis
3. **fact_check_node**: Uses FactCheckingAgent to verify and correct the draft
4. **citation_node**: Uses CitationAgent to standardize and validate citations
5. **improve_node**: Uses DraftingAgent.improve_answer() to make a final pass on the document

This workflow is managed by a StateGraph with explicit edges:
1. **StateGraph** with typed `ResearchState` containing fields for tracking state
2. **Linear Flow**: research → draft → fact_check → citation → improve → END
3. **Error Handling**: Conditional edges route to END if any node reports an error
4. **Global Variable**: `_latest_research_result` captures the final output
5. **Parameters**: `skip_fact_check` & `skip_citations` exist for backward compatibility but are forced to `False`
6. **Return Value**: Dictionary with research topic, status, research results, and final answer

## Implementation Details

### LangChain Integration

The system uses LangChain in the following ways:

- **Model Integration**: Uses `ChatGoogleGenerativeAI` to interface with Google's Gemini models:
  - `gemini-1.5-pro` for the ResearchAgent
  - `gemini-1.5-flash` for the DraftingAgent and CitationAgent
  - `gemini-2.0-flash` for the FactCheckingAgent


- **Prompt Engineering**: 
  - Uses `PromptTemplate` to create templates for each agent's chains
  - Creates prompts that define agent roles and goals

- **Chain Construction**:
  - In `BaseAgent.create_chain()`, creates simple chains using a pattern of: 
    - `prompt | self.llm` which is wrapped in a callable function
  - Returns a dictionary with the output under a specified key

- **Memory System**:
  - Simple list-based memory via `BaseAgent.add_to_memory(data)` and `clear_memory()`
  - Stores intermediate results during agent operations

- **Error Handling**:
  - Try/except blocks around chain execution and agent operations
  - Fallback behaviors when errors occur (e.g., returning original draft if correction fails)
  - Model fallback system in `BaseAgent` that tries alternative models if the primary fails

### LangGraph Workflow

The research process is implemented as a StateGraph in `graph/workflow.py`:

- **StateGraph Components**:
  - Defines a `ResearchState` TypedDict for state tracking
  - Creates nodes for each processing step (research, draft, fact-check, citation, improve)
  - Sets up linear edges between nodes and conditional edges for error handling
  - Captures final state for return to the caller

- **State Management**:
  - Passes state between nodes with each node returning an updated state
  - Uses `extract_values_from_state` to handle different state object formats
  - Uses global variable `_latest_research_result` to capture final output

- **Error Handling**:
  - Each node function has try/except blocks to catch errors
  - Conditional edges check the status and route to END on error
  - Multiple fallback mechanisms for extracting results from partial successes

### Tavily Integration

The system uses Tavily's API for web search via `utils/tavily_client.py`:

- **Search Configuration**:
  - Configurable search depth (basic or advanced)
  - Customizable result limits (`MAX_SEARCH_RESULTS=20`)
  - Support for domain inclusion/exclusion

- **API Integration**:
  - Wraps the Tavily Python client
  - Handles errors and provides fallback behavior
  - Formats results for downstream processing