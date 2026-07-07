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

    # Execute the command passed as arguments.
    # We use shell=True on Windows so that batch files like npm/npx resolve correctly.
    use_shell = os.name == "nt"
    res = subprocess.run(args, cwd=cwd, shell=use_shell)
    sys.exit(res.returncode)


if __name__ == "__main__":
    main()
