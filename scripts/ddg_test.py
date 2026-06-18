import os
import sys

# Fix path for internal imports
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(CURRENT_DIR)
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, os.path.join(PROJECT_ROOT, "backend"))

from core.utils.security import safe_http_request  # noqa: E402

url = "https://html.duckduckgo.com/html/"
params = {"q": "neon genesis evangelion"}
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

try:
    response = safe_http_request("POST", url, data=params, headers=headers, timeout=10)
    print("STATUS:", response.status_code)
    print("CONTENT LENGTH:", len(response.text))
    # Write a snippet of the HTML to inspect structure
    with open("ddg_response.html", "w", encoding="utf-8") as f:
        f.write(response.text)
    print("Done writing to ddg_response.html")
except Exception as e:
    print("ERROR:", e)
