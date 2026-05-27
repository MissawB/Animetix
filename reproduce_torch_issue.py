import sys
import os

print(f"Python version: {sys.version}")
print(f"Python executable: {sys.executable}")
print(f"Working directory: {os.getcwd()}")

try:
    import torch
    print(f"Torch version: {torch.__version__}")
    print(f"Torch file: {torch.__file__}")
    import torch._C
    print("torch._C imported successfully")
    print(f"CUDA available: {torch.cuda.is_available()}")
    if torch.cuda.is_available():
        print(f"CUDA device: {torch.cuda.get_device_name(0)}")
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
