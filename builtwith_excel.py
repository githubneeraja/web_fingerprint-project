"""
BuiltWith Excel Converter
Converts BuiltWith API technology stack data and LLM analysis into Excel format.
"""

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path
import pandas as pd
import requests
from config import BUILTWITH_API_KEY


def get_builtwith_data(domain):
    """
    Query BuiltWith API for technology information about a domain.
    
    Args:
        domain (str): The domain to query (e.g., 'example.com')
        
    Returns:
        dict: JSON response from BuiltWith API
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
    except requests.exceptions.RequestException as e:
        raise requests.exceptions.RequestException(f"BuiltWith API request failed: {e}")


def parse_timestamp(timestamp_str):
    """
    Parse timestamp string to datetime object.
    
    Args:
        timestamp_str: Timestamp string in various formats
        
    Returns:
        datetime: Parsed datetime object or None if parsing fails
    """
    if not timestamp_str:
        return None
    
    # Try common timestamp formats
    formats = [
        '%Y-%m-%d %H:%M:%S',
        '%Y-%m-%dT%H:%M:%S',
        '%Y-%m-%dT%H:%M:%SZ',
        '%Y-%m-%d',
        '%m/%d/%Y',
        '%d/%m/%Y'
    ]
    
    for fmt in formats:
        try:
            return datetime.strptime(str(timestamp_str), fmt)
        except (ValueError, TypeError):
            continue
    
    return None


def format_timestamp(dt):
    """
    Format datetime object to readable string.
    
    Args:
        dt: datetime object
        
    Returns:
        str: Formatted timestamp string or empty string
    """
    if dt is None:
        return ''
    try:
        return dt.strftime('%Y-%m-%d %H:%M:%S')
    except:
        return str(dt) if dt else ''


def extract_technology_data(builtwith_data):
    """
    Extract technology stack data from BuiltWith API response.
    
    Args:
        builtwith_data (dict): BuiltWith API JSON response
        
    Returns:
        list: List of dictionaries with technology data
    """
    rows = []
    
    # BuiltWith API typically returns data in Results array
    if 'Results' in builtwith_data:
        results = builtwith_data['Results']
    elif 'result' in builtwith_data:
        results = builtwith_data['result']
    else:
        # Try to find the main data structure
        results = builtwith_data
    
    # Handle list of results
    if isinstance(results, list):
        for result in results:
            rows.extend(_extract_from_result(result))
    elif isinstance(results, dict):
        rows.extend(_extract_from_result(results))
    
    return rows


def _extract_from_result(result):
    """
    Extract technology data from a single result object.
    
    Args:
        result (dict): Single result object from BuiltWith API
        
    Returns:
        list: List of technology data rows
    """
    rows = []
    
    # BuiltWith API structures: Paths -> Technologies
    if 'Paths' in result:
        paths = result['Paths']
        for path in paths:
            if 'Technologies' in path:
                for tech in path['Technologies']:
                    row = _create_tech_row(tech, path)
                    if row:
                        rows.append(row)
    
    # Alternative structure: Direct technologies
    elif 'Technologies' in result:
        for tech in result['Technologies']:
            row = _create_tech_row(tech, result)
            if row:
                rows.append(row)
    
    # Another structure: Categories
    elif 'Categories' in result:
        for category_name, category_data in result['Categories'].items():
            if isinstance(category_data, dict) and 'Technologies' in category_data:
                for tech in category_data['Technologies']:
                    row = _create_tech_row(tech, category_data, category_name)
                    if row:
                        rows.append(row)
    
    return rows


def _create_tech_row(tech, parent_data=None, category_override=None):
    """
    Create a row dictionary from technology data.
    
    Args:
        tech (dict): Technology object
        parent_data (dict): Parent data object (path or category)
        category_override (str): Override category name
        
    Returns:
        dict: Technology row data
    """
    # Extract category and subcategory
    category = category_override or tech.get('Category', '') or tech.get('category', '') or ''
    subcategory = tech.get('SubCategory', '') or tech.get('Subcategory', '') or tech.get('subcategory', '') or ''
    
    # Extract technology name if category/subcategory not available
    if not category:
        category = tech.get('Name', '') or tech.get('name', '') or tech.get('Technology', '') or ''
    
    # Extract counts
    live_count = tech.get('LiveCount', 0) or tech.get('live_count', 0) or tech.get('Live', 0) or 0
    dead_count = tech.get('DeadCount', 0) or tech.get('dead_count', 0) or tech.get('Dead', 0) or 0
    
    # Extract timestamps
    latest_timestamp = tech.get('Latest', '') or tech.get('latest', '') or tech.get('LatestTimestamp', '') or ''
    oldest_timestamp = tech.get('Oldest', '') or tech.get('oldest', '') or tech.get('OldestTimestamp', '') or ''
    
    # Parse timestamps
    latest_dt = parse_timestamp(latest_timestamp)
    oldest_dt = parse_timestamp(oldest_timestamp)
    
    # Format timestamps
    latest_time = format_timestamp(latest_dt)
    oldest_time = format_timestamp(oldest_dt)
    
    # Create row
    row = {
        'Category': category,
        'Subcategory': subcategory,
        'Live Count': int(live_count) if live_count else 0,
        'Dead Count': int(dead_count) if dead_count else 0,
        'Latest Timestamp': latest_timestamp,
        'Oldest Timestamp': oldest_timestamp,
        'Latest_Time': latest_time,
        'Oldest_Time': oldest_time
    }
    
    return row


def create_excel_from_data(technology_data, llm_analysis=None, output_file='builtwith_analysis.xlsx'):
    """
    Create Excel file from technology data and LLM analysis.
    
    Args:
        technology_data (list): List of technology row dictionaries
        llm_analysis (str): Optional LLM analysis text
        output_file (str): Output Excel file path
        
    Returns:
        str: Path to created Excel file
    """
    # Create DataFrame from technology data
    if not technology_data:
        # Create empty DataFrame with required columns if no data
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
    
    # Create Excel writer
    output_path = Path(output_file)
    with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
        # Write technology data to main sheet
        df.to_excel(writer, sheet_name='Technology Stack', index=False)
        
        # Write LLM analysis to separate sheet if provided
        if llm_analysis:
            analysis_df = pd.DataFrame({
                'LLM Analysis': [llm_analysis]
            })
            analysis_df.to_excel(writer, sheet_name='LLM Analysis', index=False)
        
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


def load_json_file(json_file):
    """
    Load JSON data from file.
    
    Args:
        json_file (str): Path to JSON file
        
    Returns:
        dict: Loaded JSON data
    """
    try:
        with open(json_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        raise FileNotFoundError(f"JSON file not found: {json_file}")
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON in file {json_file}: {e}")


def main():
    """Main function to handle command-line arguments and execute Excel conversion."""
    parser = argparse.ArgumentParser(
        description='Convert BuiltWith API data and LLM analysis to Excel spreadsheet.',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='Examples:\n'
               '  python builtwith_excel.py example.com\n'
               '  python builtwith_excel.py example.com --output report.xlsx\n'
               '  python builtwith_excel.py --json data.json --llm analysis.txt\n'
               '  python builtwith_excel.py example.com --json data.json --llm analysis.txt'
    )
    
    parser.add_argument(
        'domain',
        nargs='?',
        type=str,
        help='Domain to query from BuiltWith API (e.g., example.com)'
    )
    
    parser.add_argument(
        '--json',
        type=str,
        help='Path to JSON file containing BuiltWith API response (alternative to domain query)'
    )
    
    parser.add_argument(
        '--llm',
        type=str,
        help='Path to text file containing LLM analysis or LLM analysis text directly'
    )
    
    parser.add_argument(
        '--output',
        type=str,
        default='builtwith_analysis.xlsx',
        help='Output Excel file path (default: builtwith_analysis.xlsx)'
    )
    
    args = parser.parse_args()
    
    # Validate arguments
    if not args.domain and not args.json:
        parser.error("Either --domain or --json must be provided")
    
    try:
        # Get BuiltWith data
        if args.json:
            print(f"Loading BuiltWith data from: {args.json}")
            builtwith_data = load_json_file(args.json)
        else:
            domain = args.domain.strip()
            if not domain:
                print("Error: Domain cannot be empty.", file=sys.stderr)
                sys.exit(1)
            print(f"Querying BuiltWith API for domain: {domain}")
            builtwith_data = get_builtwith_data(domain)
        
        # Extract technology data
        print("Extracting technology stack data...")
        technology_data = extract_technology_data(builtwith_data)
        
        if not technology_data:
            print("Warning: No technology data found in BuiltWith response.", file=sys.stderr)
            print("The response structure may be different. Creating empty Excel with headers.")
        
        # Load LLM analysis if provided
        llm_analysis = None
        if args.llm:
            llm_path = Path(args.llm)
            if llm_path.exists():
                print(f"Loading LLM analysis from: {args.llm}")
                with open(llm_path, 'r', encoding='utf-8') as f:
                    llm_analysis = f.read()
            else:
                # Treat as direct text
                llm_analysis = args.llm
        
        # Create Excel file
        print(f"Creating Excel file: {args.output}")
        output_path = create_excel_from_data(technology_data, llm_analysis, args.output)
        
        print(f"\nSuccessfully created Excel file: {output_path}")
        print(f"  - Technology rows: {len(technology_data)}")
        if llm_analysis:
            print(f"  - LLM analysis included: Yes")
        
    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except requests.exceptions.RequestException as e:
        print(f"Error fetching BuiltWith data: {e}", file=sys.stderr)
        sys.exit(1)
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()

