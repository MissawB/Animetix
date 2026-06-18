#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""

import os  # noqa: E402
import sys  # noqa: E402


def main():
    """Run administrative tasks."""
    # Add project root to sys.path
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
    backend_path = os.path.join(project_root, "backend")
    api_path = os.path.join(backend_path, "api")

    if project_root not in sys.path:
        sys.path.insert(0, project_root)
    if backend_path not in sys.path:
        sys.path.insert(0, backend_path)
    if api_path not in sys.path:
        sys.path.insert(0, api_path)

    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "animetix_project.settings")
    try:
        from django.core.management import execute_from_command_line  # noqa: E402
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    main()
