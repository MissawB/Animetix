import re
import glob

files = glob.glob("backend/api/animetix/containers/*.py")

lazy_class_code = """
class LazyClass:
    def __init__(self, module_name, class_name):
        self.module_name = module_name
        self.class_name = class_name
        self._class = None
    
    def __call__(self, *args, **kwargs):
        if self._class is None:
            import importlib
            module = importlib.import_module(self.module_name)
            self._class = getattr(module, self.class_name)
        return self._class(*args, **kwargs)

"""

import_pattern = re.compile(r'^from (core\.domain\.\S+|adapters\.\S+|pipeline\.\S+) import (.*)$')

for filepath in files:
    if "init" in filepath: continue
    
    with open(filepath, "r", encoding="utf-8") as f:
        lines = f.readlines()

    imports_map = {}
    new_lines = []
    
    # Handle multi-line imports simply by not catching them or catching them if we can.
    # For now, let's just do single line, since multi-line is harder with regex in loop.
    # We saw one multi-line in agentic.py:
    # from core.domain.services.rag.agents import ( ... )
    # Let's read the whole content and remove multi-line imports too.
    content = "".join(lines)
    
    # regex for `from A import B, C` or `from A import ( B, C )`
    import_block_pattern = re.compile(r'^from (core\.domain\.\S+|adapters\.\S+|pipeline\.\S+) import \(?([^)]+)\)?$', re.MULTILINE)
    
    for match in import_block_pattern.finditer(content):
        module_name = match.group(1)
        classes_str = match.group(2)
        classes = [c.strip() for c in classes_str.replace('\n', '').split(',')]
        for cls in classes:
            if cls:
                imports_map[cls] = module_name
                
    # remove the imports
    content = import_block_pattern.sub('', content)

    if not imports_map:
        continue

    # Insert LazyClass helper if not already there
    if "class LazyClass:" not in content:
        insert_idx = content.find("from dependency_injector import containers, providers")
        if insert_idx != -1:
            end_of_line = content.find('\n', insert_idx) + 1
            content = content[:end_of_line] + lazy_class_code + content[end_of_line:]

    # Now replace class names with LazyClass
    for cls, mod in imports_map.items():
        pattern = r'\b' + re.escape(cls) + r'\b'
        replacement = f'LazyClass("{mod}", "{cls}")'
        content = re.sub(pattern, replacement, content)

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)

    print(f"Refactored {len(imports_map)} imports in {filepath}.")
