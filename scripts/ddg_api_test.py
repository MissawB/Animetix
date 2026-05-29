from duckduckgo_search import DDGS

try:
    with DDGS() as ddgs:
        results = list(ddgs.text("neon genesis evangelion", max_results=3))
        print("SUCCESS:", results)
except Exception as e:
    print("ERROR:", e)
