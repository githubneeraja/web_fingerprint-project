import requests
import json
from pathlib import Path
from config import BUILTWITH_API_KEY

# Replace with the domain you want to test
domain = "example.com"

url = "https://api.builtwith.com/v22/api.json"
params = {
    "KEY": BUILTWITH_API_KEY,
    "LOOKUP": domain
}

try:
    response = requests.get(url, params=params, timeout=30)
    response.raise_for_status()  # Raises error for bad status codes

    data = response.json()
    print("✅ BuiltWith API key is working!")
    print(f"Domain scanned: {domain}")
    print(f"Top-level keys in response: {list(data.keys())}")

    # Save JSON to file for Excel conversion
    output_file = Path("builtwith_response.json")
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"💾 JSON response saved to: {output_file.resolve()}")

except requests.exceptions.HTTPError as e:
    if response.status_code == 401:
        print("❌ Authentication failed. Check your API key.")
    else:
        print(f"❌ HTTP error {response.status_code}: {e}")
except requests.exceptions.RequestException as e:
    print(f"❌ Request failed: {e}")
