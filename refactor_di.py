import re

with open("backend/api/animetix/containers/core_services.py", "r", encoding="utf-8") as f:
    lines = f.readlines()

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

import_pattern = re.compile(r'^from (core\.domain\.services\S*|adapters\.\S+) import (.*)$')
# For multi-line imports, it's safer to just handle single-line since the output above showed they were all single line imports.

imports_map = {}
new_lines = []

for line in lines:
    match = import_pattern.match(line.strip())
    if match:
        module_name = match.group(1)
        classes_str = match.group(2)
        classes = [c.strip() for c in classes_str.split(',')]
        for cls in classes:
            imports_map[cls] = module_name
    else:
        new_lines.append(line)

content = "".join(new_lines)

# Insert LazyClass helper after 'from dependency_injector import containers, providers'
insert_idx = content.find("from dependency_injector import containers, providers")
if insert_idx != -1:
    end_of_line = content.find('\n', insert_idx) + 1
    content = content[:end_of_line] + lazy_class_code + content[end_of_line:]

# Now replace class names with LazyClass
for cls, mod in imports_map.items():
    # Only replace whole words
    # Like providers.Singleton(GameService, ...) -> providers.Singleton(LazyClass("module", "GameService"), ...)
    pattern = r'\b' + re.escape(cls) + r'\b'
    replacement = f'LazyClass("{mod}", "{cls}")'
    content = re.sub(pattern, replacement, content)

with open("backend/api/animetix/containers/core_services.py", "w", encoding="utf-8") as f:
    f.write(content)

print(f"Refactored {len(imports_map)} imports to LazyClass.")
