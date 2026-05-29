from ddgs import DDGS

try:
    with DDGS() as ddgs:
        results = list(ddgs.text("neon genesis evangelion", max_results=2))
        print("KEYS:", results[0].keys() if results else "empty")
        print("SAMPLE:", {k: v.encode('ascii', 'ignore').decode('ascii') for k, v in results[0].items()} if results else "empty")
except Exception as e:
    print("ERROR:", e)
