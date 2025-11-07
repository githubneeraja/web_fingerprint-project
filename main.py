"""
Main script for BuiltWith analysis workflow.
Queries BuiltWith API, analyzes with Ollama, and optionally exports to Excel.
"""

import argparse
import json
import sys
from pathlib import Path
from datetime import datetime
import requests
import pandas as pd
from ollama import chat
from ollama import RequestError, ResponseError
from config import BUILTWITH_API_KEY

# Import functions from builtwith_excel.py
from builtwith_excel import extract_technology_data, create_excel_from_data


def get_builtwith_data(domain):
    """
    Query BuiltWith API for technology information about a domain.
    
    Args:
        domain (str): The domain to query (e.g., 'example.com')
        
    Returns:
        dict: JSON response from BuiltWith API
        
    Raises:
        requests.exceptions.RequestException: If the API request fails
    """
    url = 'https://api.builtwith.com/v22/api.json'
    
    params = {
        'KEY': BUILTWITH_API_KEY,
        'LOOKUP': domain
    }
    
    try:
        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.Timeout:
        raise requests.exceptions.RequestException("Request timed out. Please try again.")
    except requests.exceptions.HTTPError as e:
        if response.status_code == 401:
            raise requests.exceptions.RequestException("Authentication failed. Please check your API key.")
        elif response.status_code == 404:
            raise requests.exceptions.RequestException(f"Domain '{domain}' not found or invalid.")
        else:
            raise requests.exceptions.RequestException(f"HTTP error {response.status_code}: {e}")
    except requests.exceptions.RequestException as e:
        raise requests.exceptions.RequestException(f"Request failed: {e}")


def analyze_with_ollama(builtwith_result, model='llama3', stream=False):
    """
    Analyze BuiltWith JSON result using Ollama model.
    
    Args:
        builtwith_result (dict): JSON result from BuiltWith API
        model (str): Ollama model to use (e.g., 'llama3', 'tinyllama')
        stream (bool): Whether to stream the response
        
    Returns:
        str: Analysis from Ollama model
        
    Raises:
        RequestError: If the model is not available or request fails
        ResponseError: If Ollama returns an error
    """
    # Format the BuiltWith result as JSON string
    builtwith_json = json.dumps(builtwith_result, indent=2, ensure_ascii=False)
    
    # Create the prompt as specified
    prompt = f'Analyze the following BuiltWith result and provide insights:\n\n{builtwith_json}.'
    
    try:
        if stream:
            # Stream the response
            print("Analyzing with Ollama...\n")
            print("=" * 80)
            full_response = ""
            for chunk in chat(
                model=model,
                messages=[{'role': 'user', 'content': prompt}],
                stream=True
            ):
                content = chunk['message']['content']
                print(content, end='', flush=True)
                full_response += content
            print("\n" + "=" * 80)
            return full_response
        else:
            # Get complete response
            print(f"Analyzing with Ollama ({model})...\n")
            response = chat(
                model=model,
                messages=[{'role': 'user', 'content': prompt}]
            )
            analysis = response['message']['content']
            print("\n" + "=" * 80)
            print("Ollama Analysis:")
            print("=" * 80)
            print(analysis)
            print("=" * 80)
            return analysis
    except RequestError as e:
        raise RequestError(f"Ollama request failed: {e}. Make sure Ollama is running and the model '{model}' is available.")
    except ResponseError as e:
        raise ResponseError(f"Ollama response error: {e}")
    except Exception as e:
        raise Exception(f"Unexpected error communicating with Ollama: {e}")


def create_excel_with_ollama_append(technology_data, llm_analysis, output_file):
    """
    Create Excel file with technology data and append Ollama analysis at the end.
    
    Args:
        technology_data (list): List of technology row dictionaries
        llm_analysis (str): Ollama analysis text to append
        output_file (str): Output Excel file path
        
    Returns:
        str: Path to created Excel file
    """
    # Create DataFrame from technology data
    if not technology_data:
        df = pd.DataFrame(columns=[
            'Category',
            'Subcategory',
            'Live Count',
            'Dead Count',
            'Latest Timestamp',
            'Oldest Timestamp',
            'Latest_Time',
            'Oldest_Time'
        ])
    else:
        df = pd.DataFrame(technology_data)
    
    # Ensure all required columns exist
    required_columns = [
        'Category',
        'Subcategory',
        'Live Count',
        'Dead Count',
        'Latest Timestamp',
        'Oldest Timestamp',
        'Latest_Time',
        'Oldest_Time'
    ]
    
    for col in required_columns:
        if col not in df.columns:
            df[col] = ''
    
    # Reorder columns to match specification
    df = df[required_columns]
    
    # Append Ollama analysis as a row at the end
    if llm_analysis:
        # Split analysis into lines and add as rows
        analysis_lines = llm_analysis.split('\n')
        
        # Add separator row
        separator_row = pd.DataFrame({
            'Category': ['---'],
            'Subcategory': ['Ollama Analysis'],
            'Live Count': [''],
            'Dead Count': [''],
            'Latest Timestamp': [''],
            'Oldest Timestamp': [''],
            'Latest_Time': [''],
            'Oldest_Time': ['']
        })
        
        # Add analysis rows
        analysis_rows = []
        for line in analysis_lines:
            if line.strip():  # Only add non-empty lines
                analysis_rows.append({
                    'Category': '',
                    'Subcategory': line.strip(),
                    'Live Count': '',
                    'Dead Count': '',
                    'Latest Timestamp': '',
                    'Oldest Timestamp': '',
                    'Latest_Time': '',
                    'Oldest_Time': ''
                })
        
        if analysis_rows:
            analysis_df = pd.DataFrame(analysis_rows)
            df = pd.concat([df, separator_row, analysis_df], ignore_index=True)
    
    # Create Excel writer
    output_path = Path(output_file)
    with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
        # Write technology data with appended analysis to main sheet
        df.to_excel(writer, sheet_name='Technology Stack', index=False)
        
        # Also write LLM analysis to separate sheet for better readability
        if llm_analysis:
            analysis_df_sheet = pd.DataFrame({
                'LLM Analysis': [llm_analysis]
            })
            analysis_df_sheet.to_excel(writer, sheet_name='LLM Analysis', index=False)
        
        # Format the Excel file
        workbook = writer.book
        tech_sheet = writer.sheets['Technology Stack']
        
        # Auto-adjust column widths
        for column in tech_sheet.columns:
            max_length = 0
            column_letter = column[0].column_letter
            for cell in column:
                try:
                    if len(str(cell.value)) > max_length:
                        max_length = len(str(cell.value))
                except:
                    pass
            adjusted_width = min(max_length + 2, 50)
            tech_sheet.column_dimensions[column_letter].width = adjusted_width
        
        # Format header row
        from openpyxl.styles import Font, PatternFill, Alignment
        
        header_fill = PatternFill(start_color='366092', end_color='366092', fill_type='solid')
        header_font = Font(bold=True, color='FFFFFF')
        
        for cell in tech_sheet[1]:
            cell.fill = header_fill
            cell.font = header_font
            cell.alignment = Alignment(horizontal='center', vertical='center')
    
    return str(output_path)


def main():
    """Main function to handle command-line arguments and execute workflow."""
    parser = argparse.ArgumentParser(
        description='Query BuiltWith API, analyze with Ollama, and optionally export to Excel.',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='Examples:\n'
               '  python main.py xyz.com\n'
               '  python main.py xyz.com --excel\n'
               '  python main.py xyz.com --excel --model tinyllama\n'
               '  python main.py xyz.com --excel --output report.xlsx'
    )
    
    parser.add_argument(
        'domain',
        type=str,
        help='The domain to query and analyze (e.g., xyz.com)'
    )
    
    parser.add_argument(
        '--excel',
        action='store_true',
        help='Export results to Excel file (appends Ollama analysis at the end)'
    )
    
    parser.add_argument(
        '--model',
        type=str,
        default='llama3',
        help='Ollama model to use (default: llama3). Examples: llama3, tinyllama, llama3.2'
    )
    
    parser.add_argument(
        '--output',
        type=str,
        help='Output Excel file path (only used with --excel flag, default: {domain}_analysis.xlsx)'
    )
    
    parser.add_argument(
        '--stream',
        action='store_true',
        help='Stream the Ollama response (shows response as it generates)'
    )
    
    args = parser.parse_args()
    
    # Validate domain
    domain = args.domain.strip()
    if not domain:
        print("Error: Domain cannot be empty.", file=sys.stderr)
        sys.exit(1)
    
    try:
        # Step 1: Query BuiltWith API
        print(f"Querying BuiltWith API for domain: {domain}")
        builtwith_data = get_builtwith_data(domain)
        
        # Check for errors in BuiltWith response
        if 'Errors' in builtwith_data:
            print("\nBuiltWith API returned errors:")
            print(json.dumps(builtwith_data['Errors'], indent=2))
            print("\nNote: Analysis will still proceed with available data.\n")
        
        # Step 2: Analyze with Ollama
        llm_analysis = None
        try:
            print("\nAnalyzing results with Ollama...")
            llm_analysis = analyze_with_ollama(builtwith_data, model=args.model, stream=args.stream)
        except (RequestError, ResponseError, Exception) as e:
            print(f"\nWarning: Could not analyze with Ollama: {e}", file=sys.stderr)
            if args.excel:
                print("Continuing with Excel export without Ollama analysis...", file=sys.stderr)
            else:
                print("\nTip: Make sure Ollama is running. Start it with: ollama serve", file=sys.stderr)
                print(f"Tip: Make sure the model '{args.model}' is available. Pull it with: ollama pull {args.model}", file=sys.stderr)
                sys.exit(1)
        
        # Step 3: Export to Excel if --excel flag is set
        if args.excel:
            print("\nExtracting technology stack data...")
            technology_data = extract_technology_data(builtwith_data)
            
            # Determine output file name
            if args.output:
                output_file = args.output
            else:
                # Generate filename from domain
                safe_domain = domain.replace('.', '_').replace('/', '_')
                output_file = f"{safe_domain}_analysis.xlsx"
            
            print(f"Creating Excel file: {output_file}")
            output_path = create_excel_with_ollama_append(technology_data, llm_analysis, output_file)
            
            print(f"\nSuccessfully created Excel file: {output_path}")
            print(f"  - Technology rows: {len(technology_data)}")
            print(f"  - Ollama analysis appended: {'Yes' if llm_analysis else 'No (Ollama unavailable)'}")
        
    except requests.exceptions.RequestException as e:
        print(f"Error fetching BuiltWith data: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()

