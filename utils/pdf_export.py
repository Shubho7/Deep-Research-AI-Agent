import os
import re
from datetime import datetime
from fpdf import FPDF

def export_to_pdf(research_topic, final_answer, output_path=None):
    """
    Export research results to a PDF file.
    
    Args:
        research_topic (str): The research topic
        final_answer (str): The final research answer
        output_path (str, optional): The output file path. If None, a default path will be generated.
        
    Returns:
        str: The path to the saved PDF file
    """
    print("Starting PDF export process...")
    
    def clean_text_for_pdf(text):
        if not text:
            return ""
        # Replace common Unicode characters with ASCII equivalents
        replacements = {
            '\u2014': '--',  # em dash
            '\u2013': '-',   # en dash
            '\u2018': "'",   # left single quote
            '\u2019': "'",   # right single quote
            '\u201c': '"',   # left double quote
            '\u201d': '"',   # right double quote
            '\u2022': '*',   # bullet
            '\u2026': '...',  # ellipsis
            '\u00a0': ' ',   # non-breaking space
        }
        
        for char, replacement in replacements.items():
            text = text.replace(char, replacement)
        
        # Replace any remaining non-latin1 characters with '?'
        text = re.sub(r'[^\x00-\xFF]', '?', text)
        
        return text
    
    # Clean the input text
    research_topic = clean_text_for_pdf(research_topic)
    final_answer = clean_text_for_pdf(final_answer)
    
    # Create PDF object
    pdf = FPDF()
    pdf.add_page()
    
    pdf.set_font("Arial", "B", 20)  
    pdf.cell(0, 10, f"{research_topic.upper()}", 0, 1, "C")
    pdf.ln(10)
    
    # Process final answer to make subheadings bold and add clickable links
    lines = final_answer.split('\n')
    pdf.set_font("Arial", "", 12)
    
    # Regular expression to detect URLs
    url_pattern = re.compile(r'https?://[\w\.-]+(?:/[\w\.-]+)*/?(?:\?[\w=&\.-]+)?')
    
    for line in lines:
        stripped_line = line.strip()
        
        is_heading = False
        if stripped_line:
            if (not stripped_line[-1] in '.,:;?!' and len(stripped_line) < 60) or \
               stripped_line.startswith('#') or \
               re.match(r'^\d+\.\s+\w+', stripped_line):
                is_heading = True
        
        if is_heading:
            pdf.set_font("Arial", "B", 14)  
            pdf.multi_cell(0, 10, stripped_line)
            pdf.set_font("Arial", "", 12)  
        else:
            # Process line for URLs and make them clickable
            url_matches = list(url_pattern.finditer(line))
            
            if url_matches:
                # Line contains URLs, process it in segments
                last_end = 0
                for match in url_matches:
                    # Print text before the URL
                    if match.start() > last_end:
                        pdf.write(5, line[last_end:match.start()])
                    
                    # Add the URL as a clickable link
                    url = match.group(0)
                    pdf.set_text_color(0, 0, 255) 
                    pdf.write(5, url, url)  
                    pdf.set_text_color(0, 0, 0)  
                    
                    last_end = match.end()
                
                # Print any remaining text after the last URL
                if last_end < len(line):
                    pdf.write(5, line[last_end:])
                
                pdf.ln()
            else:   
                pdf.multi_cell(0, 10, line)
    
    # Add acknowledgment at the end
    pdf.ln(10)
    pdf.set_font("Arial", "I", 10)
    pdf.cell(0, 10, "By DeepResearchAI", 0, 1, "R")
    
    # Generate default output path if not provided
    if not output_path:
        # Create sanitized filename from research topic
        sanitized_topic = "".join(c if c.isalnum() else "_" for c in research_topic)
        sanitized_topic = sanitized_topic[:50]
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        # Use current working directory for default path
        output_path = os.path.join(os.getcwd(), f"research_{sanitized_topic}_{timestamp}.pdf")
    
    # Ensure the directory exists
    output_dir = os.path.dirname(output_path)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # Save the PDF
    try:
        pdf.output(output_path)
        print(f"PDF successfully saved to: {output_path}")
    except Exception as e:
        print(f"Error during PDF output operation: {e}")
        # Try with absolute path if relative path failed
        if not os.path.isabs(output_path):
            try:
                abs_path = os.path.abspath(output_path)
                print(f"Trying with absolute path: {abs_path}")
                pdf.output(abs_path)
                output_path = abs_path
                print(f"PDF successfully saved to: {output_path}")
            except Exception as inner_e:
                print(f"Failed with absolute path too: {inner_e}")
                raise Exception(f"Could not save PDF: {str(e)} and then {str(inner_e)}")
        else:
            # If it was already an absolute path, just re-raise the exception
            raise
    
    return output_path