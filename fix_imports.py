import os
import re

base_dir = r'frontend/src/pages'
pattern = re.compile(r'from\s+["\']\.\.\/\.\.\/\.\.\/(store|components|utils|api|types|features|assets)')

for root, dirs, files in os.walk(base_dir):
    # Only process subfolders of src/pages
    if root == base_dir:
        continue
    
    for file in files:
        if file.endswith('.tsx'):
            file_path = os.path.join(root, file)
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            new_content = pattern.sub(lambda m: f'from "../../{m.group(1)}', content)
            
            if content != new_content:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(new_content)
                print(f"Updated: {file_path}")
