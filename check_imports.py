
import sys
import os
sys.path.insert(0, os.path.abspath("src/backend"))
sys.path.insert(0, os.path.abspath("src"))

try:
    import animetix.views.common
    print("SUCCESS: animetix.views.common imported")
    print(f"File: {animetix.views.common.__file__}")
except Exception as e:
    print(f"FAILED: {e}")
    import traceback
    traceback.print_exc()
