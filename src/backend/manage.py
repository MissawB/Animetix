#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import os
import sys


def main():
    """Run administrative tasks."""
    # Add project root to sys.path
    import sys
    import os
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
    src_path = os.path.join(project_root, "src")
    
    if project_root not in sys.path:
        sys.path.insert(0, project_root)
    if src_path not in sys.path:
        sys.path.insert(0, src_path)
        
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'animetix_project.settings')
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == '__main__':
    main()
