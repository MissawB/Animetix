import os
import re

routes_dir = r'frontend/src/features'

for root, dirs, files in os.walk(routes_dir):
    if root.endswith('routes'):
        # Get module name (one level above 'routes')
        module = os.path.basename(os.path.dirname(root))
        
        for file in files:
            if file.endswith('.tsx'):
                file_path = os.path.join(root, file)
                
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # 1. Handle import('../Page') -> import('../../../pages/module/Page')
                # Avoid matching if it already starts with ../../../pages/
                new_content = re.sub(r"import\(['\"](?!\.\.\/\.\.\/\.\.\/pages\/)\.\.\/([A-Za-z0-9_-]+)['\"]\)", 
                                     rf"import('../../../pages/{module}/\1')", content)
                
                # 2. Handle import('../../otherModule/Page') -> import('../../../pages/otherModule/Page')
                new_content = re.sub(r"import\(['\"](?!\.\.\/\.\.\/\.\.\/pages\/)\.\.\/\.\.\/([A-Za-z0-9_-]+\/[A-Za-z0-9_-]+)['\"]\)", 
                                     r"import('../../../pages/\1')", new_content)

                if content != new_content:
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(new_content)
                    print(f"Updated routes: {file_path}")
