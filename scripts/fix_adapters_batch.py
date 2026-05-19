import os
import inspect
import sys
from abc import ABC, abstractmethod

# Path setup
base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(os.path.join(base_dir, "src"))

from core.ports.inference_port import InferencePort

def fix_adapter(file_path):
    print(f"Fixing {file_path}...")
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Identify class name
    import re
    class_match = re.search(r"class (\w+)\(InferencePort\):", content)
    if not class_match:
        print(f"  Skipping {file_path}: class not found.")
        return

    class_name = class_match.group(1)
    
    # Check for missing methods
    abstract_methods = list(InferencePort.__abstractmethods__)
    
    stub_template = """
    def {name}(self, *args, **kwargs):
        raise NotImplementedError("{name} not implemented in {class_name}")
"""
    
    stubs_to_add = []
    for method in abstract_methods:
        # Utiliser regex pour s'assurer que c'est le nom exact de la méthode
        if not re.search(fr"def {method}\b", content):
            stubs_to_add.append(method)

    if not stubs_to_add:
        print(f"  No missing methods for {class_name}.")
        return

    print(f"  Adding {len(stubs_to_add)} missing methods to {class_name}...")
    
    # Add stubs before health_check or at the end
    new_stubs = "".join([stub_template.format(name=m, class_name=class_name) for m in stubs_to_add])
    
    if "def health_check" in content:
        content = content.replace("def health_check", new_stubs + "\n    def health_check")
    else:
        content += "\n" + new_stubs

    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)

adapters_dir = os.path.join(base_dir, "src", "adapters", "inference")
for filename in os.listdir(adapters_dir):
    if filename.endswith("_adapter.py"):
        fix_adapter(os.path.join(adapters_dir, filename))
