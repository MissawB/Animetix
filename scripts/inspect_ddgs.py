from duckduckgo_search import DDGS
import inspect

with DDGS() as ddgs:
    print(
        "DDGS METHODS:",
        [m[0] for m in inspect.getmembers(ddgs) if not m[0].startswith("_")],
    )
    try:
        res = ddgs.text("anime", max_results=5)
        print("RES TYPE:", type(res))
        print("RES CONTENT:", list(res))
    except Exception as e:
        print("ERROR:", e)
