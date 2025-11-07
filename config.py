"""
Configuration module for BuiltWith API client.
Loads API key from environment variables (.env file).
"""

import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# BuiltWith API key
BUILTWITH_API_KEY = os.getenv('BUILTWITH_API_KEY')

if not BUILTWITH_API_KEY:
    raise ValueError(
        "BUILTWITH_API_KEY not found in environment variables. "
        "Please ensure your .env file contains: BUILTWITH_API_KEY=your_key"
    )

