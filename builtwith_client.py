"""
BuiltWith API Client
Queries the BuiltWith API for technology information about a domain.
"""

import argparse
import json
import sys
import requests
from config import BUILTWITH_API_KEY


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
    # BuiltWith API endpoint
    url = f'https://api.builtwith.com/v22/api.json'
    
    # API parameters
    params = {
        'KEY': BUILTWITH_API_KEY,
        'LOOKUP': domain
    }
    
    try:
        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()  # Raise an exception for bad status codes
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


def print_json_readable(data):
    """
    Print JSON data in a readable, formatted way.
    
    Args:
        data: JSON-serializable data structure
    """
    print(json.dumps(data, indent=2, ensure_ascii=False))


def main():
    """Main function to handle command-line arguments and execute API query."""
    parser = argparse.ArgumentParser(
        description='Query BuiltWith API for domain technology information.',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='Example usage:\n  python builtwith_client.py example.com'
    )
    
    parser.add_argument(
        'domain',
        type=str,
        help='The domain to query (e.g., example.com)'
    )
    
    parser.add_argument(
        '--output',
        type=str,
        choices=['json', 'pretty'],
        default='pretty',
        help='Output format: json (compact) or pretty (formatted, default)'
    )
    
    args = parser.parse_args()
    
    # Validate domain format (basic check)
    domain = args.domain.strip()
    if not domain:
        print("Error: Domain cannot be empty.", file=sys.stderr)
        sys.exit(1)
    
    try:
        print(f"Querying BuiltWith API for domain: {domain}\n")
        data = get_builtwith_data(domain)
        
        if args.output == 'json':
            print(json.dumps(data, ensure_ascii=False))
        else:
            print_json_readable(data)
            
    except requests.exceptions.RequestException as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON response from API: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()

