import os
import glob
import re
import shutil

# 1. Create dependencies.py
deps_path = 'src/backend/animetix/api/dependencies.py'
os.makedirs(os.path.dirname(deps_path), exist_ok=True)

deps_content = """from dependency_injector.wiring import inject, Provide
from animetix.containers import Container
from core.domain.services.game_session_service import GameSessionService

@inject
def get_session_service(request, 
                        session_factory: GameSessionService = Provide[Container.game_session_service_factory],
                        port_factory = Provide[Container.session_state_adapter_factory]):
    port = port_factory(session=request.session)
    return session_factory(state_port=port)
"""

with open(deps_path, 'w', encoding='utf-8') as f:
    f.write(deps_content)

# 2. Refactor imports in all files
target_dirs = ['src/backend/animetix/api/**/*.py', 'src/backend/animetix/views/**/*.py']

files_to_process = []
for d in target_dirs:
    files_to_process.extend(glob.glob(d, recursive=True))

for filepath in set(files_to_process):
    if filepath.replace('\\', '/') == deps_path.replace('\\', '/'):
        continue
        
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
        
    # Replace relative and absolute imports
    new_content = re.sub(
        r'from (\.\.+|\.)utils\.session import get_session_service', 
        r'from animetix.api.dependencies import get_session_service', 
        content
    )
    new_content = re.sub(
        r'from animetix\.utils\.session import get_session_service', 
        r'from animetix.api.dependencies import get_session_service', 
        new_content
    )
    
    if content != new_content:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(new_content)
        print(f"Updated {filepath}")

# 3. Delete utils/session.py
session_py_path = 'src/backend/animetix/utils/session.py'
if os.path.exists(session_py_path):
    os.remove(session_py_path)
    print(f"Deleted {session_py_path}")

# Delete the utils folder if it's empty (except __pycache__/__init__.py)
utils_dir = 'src/backend/animetix/utils'
if os.path.exists(utils_dir):
    try:
        shutil.rmtree(utils_dir, ignore_errors=True)
    except:
        pass
