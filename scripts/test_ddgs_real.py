from ddgs import DDGS

try:
    with DDGS() as ddgs:
        results = list(ddgs.text("neon genesis evangelion", max_results=3))
        print("SUCCESS:")
        for r in results:
            print("-", r)
except Exception as e:
    print("ERROR:", e)
