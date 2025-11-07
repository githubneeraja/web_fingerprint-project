"""
Example script demonstrating how to securely load and use BuiltWith API credentials.
This script shows the proper way to access API keys from environment variables.
"""

import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Securely retrieve the API key
api_key = os.getenv('BUILTWITH_API_KEY')

if api_key:
    print("✓ API key loaded successfully from .env file")
    print(f"✓ API key (first 10 chars): {api_key[:10]}...")
    print("\nYou can now use this API key with the BuiltWith API.")
    print("Example usage:")
    print(f"  headers = {{'X-API-KEY': '{api_key[:10]}...'}}")
else:
    print("✗ Error: BUILTWITH_API_KEY not found in .env file")
    print("Please ensure your .env file contains: BUILTWITH_API_KEY=your_key")

