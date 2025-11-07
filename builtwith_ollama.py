"""
BuiltWith + Ollama Integration
Queries BuiltWith API and analyzes the results using Ollama models.
"""

import argparse
import json
import sys
import requests
from ollama import chat
from ollama import ResponseError, RequestError
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
    url = 'https://api.builtwith.com/v22/api.json'
    
    # API parameters
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
            return response['message']['content']
    except RequestError as e:
        raise RequestError(f"Ollama request failed: {e}. Make sure Ollama is running and the model '{model}' is available.")
    except ResponseError as e:
        raise ResponseError(f"Ollama response error: {e}")
    except Exception as e:
        raise Exception(f"Unexpected error communicating with Ollama: {e}")


def main():
    """Main function to handle command-line arguments and execute analysis."""
    parser = argparse.ArgumentParser(
        description='Query BuiltWith API and analyze results with Ollama.',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='Examples:\n'
               '  python builtwith_ollama.py example.com\n'
               '  python builtwith_ollama.py example.com --model tinyllama\n'
               '  python builtwith_ollama.py example.com --model llama3 --stream'
    )
    
    parser.add_argument(
        'domain',
        type=str,
        help='The domain to query and analyze (e.g., example.com)'
    )
    
    parser.add_argument(
        '--model',
        type=str,
        default='llama3',
        help='Ollama model to use (default: llama3). Examples: llama3, tinyllama, llama3.2'
    )
    
    parser.add_argument(
        '--stream',
        action='store_true',
        help='Stream the Ollama response (shows response as it generates)'
    )
    
    parser.add_argument(
        '--show-json',
        action='store_true',
        help='Show the raw BuiltWith JSON before analysis'
    )
    
    args = parser.parse_args()
    
    # Validate domain format
    domain = args.domain.strip()
    if not domain:
        print("Error: Domain cannot be empty.", file=sys.stderr)
        sys.exit(1)
    
    try:
        # Step 1: Get BuiltWith data
        print(f"Querying BuiltWith API for domain: {domain}")
        builtwith_data = get_builtwith_data(domain)
        
        # Check for errors in BuiltWith response
        if 'Errors' in builtwith_data:
            print("\nBuiltWith API returned errors:")
            print(json.dumps(builtwith_data['Errors'], indent=2))
            print("\nNote: Analysis will still proceed with available data.\n")
        
        # Optionally show the raw JSON
        if args.show_json:
            print("\n" + "=" * 80)
            print("BuiltWith JSON Result:")
            print("=" * 80)
            print(json.dumps(builtwith_data, indent=2, ensure_ascii=False))
            print("=" * 80 + "\n")
        
        # Step 2: Analyze with Ollama
        analysis = analyze_with_ollama(builtwith_data, model=args.model, stream=args.stream)
        
        # Print non-streaming response
        if not args.stream:
            print("\n" + "=" * 80)
            print("Ollama Analysis:")
            print("=" * 80)
            print(analysis)
            print("=" * 80)
        
    except requests.exceptions.RequestException as e:
        print(f"Error fetching BuiltWith data: {e}", file=sys.stderr)
        sys.exit(1)
    except RequestError as e:
        print(f"Error: {e}", file=sys.stderr)
        print("\nTip: Make sure Ollama is running. Start it with: ollama serve", file=sys.stderr)
        print(f"Tip: Make sure the model '{args.model}' is available. Pull it with: ollama pull {args.model}", file=sys.stderr)
        sys.exit(1)
    except ResponseError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()

