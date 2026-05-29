import httpx

url = "https://html.duckduckgo.com/html/"
params = {"q": "neon genesis evangelion"}
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

try:
    response = httpx.post(url, data=params, headers=headers, timeout=10, follow_redirects=True)
    print("STATUS:", response.status_code)
    print("CONTENT LENGTH:", len(response.text))
    # Write a snippet of the HTML to inspect structure
    with open("ddg_response.html", "w", encoding="utf-8") as f:
        f.write(response.text)
    print("Done writing to ddg_response.html")
except Exception as e:
    print("ERROR:", e)
