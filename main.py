"""
Main entry point for the DeepResearchAI application.
"""
import argparse
import json
import os
from graph.workflow import run_research_workflow
from utils.config import validate_config
from utils.pdf_export import export_to_pdf

def main():
    """Main entry point for the application."""
    
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="DeepResearchAI: AI-powered deep research system using Google Gemini")
    parser.add_argument("--topic", type=str, help="The research topic")
    parser.add_argument("--depth", type=str, choices=["basic", "advanced"], default="basic", help="The research depth (basic or advanced)")
    parser.add_argument("--queries", type=int, default=3, help="Number of search queries to generate")
    parser.add_argument("--output", type=str, help="Output file path for the research results (JSON)")
    args = parser.parse_args()
    
    # Validate configuration
    try:
        validate_config()
    except Exception as e:
        print(f"Configuration error: {e}")
        return
    
    # Interactive mode if no topic provided
    if not args.topic:
        print("Welcome to DeepResearchAI")
        print("------------------------------------------------")
        args.topic = input("Enter research topic: ")
        depth_input = input("Research depth (basic/advanced) [default: basic]: ")
        args.depth = depth_input if depth_input in ["basic", "advanced"] else "basic"
        queries_input = input("Number of search queries [default: 3]: ")
        try:
            args.queries = int(queries_input) if queries_input.strip() else 3
        except ValueError:
            args.queries = 3
    
    # Run the research workflow
    print(f"\nResearch topic: {args.topic}")
    print(f"Research depth: {args.depth}")
    print(f"Number of queries: {args.queries}")
    print("\nStarting the research workflow\n")
    
    result = run_research_workflow(
        research_topic=args.topic,
        research_depth=args.depth,
        num_queries=args.queries
    )
    
    # Print the result
    if result.get("status") == "complete" and "final_answer" in result:
        print("\n=== RESEARCH COMPLETE ===\n")
        print(f"Research topic: {result['research_topic']}")
        print("\n=== FINAL ANSWER ===\n")
        print(result["final_answer"])
    else:
        print(f"\nResearch status: {result.get('status', 'unknown')}")
        if "error" in result and result["error"]:
            print(f"Error: {result['error']}")
        if "final_answer" in result and result["final_answer"]:
            print("\n=== FINAL ANSWER ===\n")
            print(result["final_answer"])
    
    # Save to output file if specified
    if args.output:
        with open(args.output, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2)
        print(f"\nResults saved to {args.output}")
    
    # Ask user if they want to save as PDF
    if result.get("status") == "complete" and "final_answer" in result:
        save_pdf = input("\nWould you like to save the research as a PDF? (y/n): ").lower().strip()
        if save_pdf == 'y' or save_pdf == 'yes':
            pdf_path = input("Enter PDF output path (leave blank for auto-generated filename): ").strip()
            try:
                saved_path = export_to_pdf(
                    research_topic=result['research_topic'],
                    final_answer=result['final_answer'],
                    output_path=pdf_path if pdf_path else None
                )
                print(f"\nPDF successfully saved to: {saved_path}")
            except Exception as e:
                print(f"\nError saving PDF: {e}")

if __name__ == "__main__":
    main()