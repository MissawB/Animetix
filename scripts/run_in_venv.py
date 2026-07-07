import os
import subprocess
import sys


def main():
    args = sys.argv[1:]
    cwd = None
    if args and args[0] == "--cwd":
        if len(args) < 2:
            print("Error: --cwd requires a directory path", file=sys.stderr)
            sys.exit(1)
        cwd = args[1]
        args = args[2:]

    # Resolve cwd to an absolute path relative to repository root
    script_dir = os.path.dirname(os.path.abspath(__file__))
    repo_root = os.path.dirname(script_dir)
    if cwd:
        cwd = os.path.abspath(os.path.join(repo_root, cwd))

    # Detect the correct virtualenv python relative to repository root
    venv_dir = os.path.join(repo_root, ".venv")
    if not os.path.exists(venv_dir):
        print(f"Error: Virtual environment not found at {venv_dir}", file=sys.stderr)
        sys.exit(1)

    venv_bin = "Scripts" if os.name == "nt" else "bin"
    python_exe = os.path.join(venv_dir, venv_bin, "python")
    if os.name == "nt" and not python_exe.endswith(".exe"):
        python_exe += ".exe"

    if not os.path.exists(python_exe):
        print(f"Error: Python executable not found at {python_exe}", file=sys.stderr)
        sys.exit(1)

    # Execute the command passed as arguments
    cmd_args = [python_exe] + args
    res = subprocess.run(cmd_args, cwd=cwd)
    sys.exit(res.returncode)


if __name__ == "__main__":
    main()
