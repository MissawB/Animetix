import os
import re

base_dir = r'frontend/src/pages'
# Capture the quote type
pattern = re.compile(r'from\s+(["\'])\.\.\/\.\.\/\.\.\/(store|components|utils|api|types|features|assets)')

for root, dirs, files in os.walk(base_dir):
    if root == base_dir:
        continue
    
    for file in files:
        if file.endswith('.tsx'):
            file_path = os.path.join(root, file)
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Use the captured quote type in replacement
            # Note: We also need to handle the case where it's already broken (mismatched)
            # Actually, I'll just match the current broken state too.
            broken_pattern = re.compile(r'from\s+["\']\.\.\/(store|components|utils|api|types|features|assets)')
            # Wait, the broken state is from "../../components... '
            # Let's just fix it by matching the folder and looking at the end quote.
            
            # Improved regex to match the whole import string to be safe
            import_pattern = re.compile(r'from\s+(["\'])\.\.(?:\/\.\.)*\/(store|components|utils|api|types|features|assets)([^"\']*)(["\'])')
            
            def replace_import(m):
                quote_start = m.group(1)
                folder = m.group(2)
                rest = m.group(3)
                quote_end = m.group(4)
                # For pages subfolders, it should be ../../
                return f'from {quote_start}../../{folder}{rest}{quote_start}'

            new_content = import_pattern.sub(replace_import, content)
            
            if content != new_content:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(new_content)
                print(f"Updated: {file_path}")
