import os
import shutil
import subprocess
import sys


def run_command(cmd, cwd=None, shell=False):
    # Try resolving executable on PATH
    resolved = shutil.which(cmd[0])
    if resolved:
        cmd[0] = resolved

    res = subprocess.run(cmd, cwd=cwd, shell=shell)
    if res.returncode != 0:
        print(f"Error running: {' '.join(cmd)}")
        sys.exit(res.returncode)


def main():
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    # Use virtual environment python if it exists to ensure packages are available
    if os.name == "nt":
        venv_python = os.path.join(project_root, ".venv", "Scripts", "python.exe")
    else:
        venv_python = os.path.join(project_root, ".venv", "bin", "python")

    python_exe = venv_python if os.path.exists(venv_python) else sys.executable

    print("[1/3] Extracting OpenAPI schema from Django...")
    run_command(
        [
            python_exe,
            os.path.join("backend", "api", "manage.py"),
            "spectacular",
            "--file",
            "schema.yaml",
        ],
        cwd=project_root,
    )

    print("[2/3] Generating TypeScript types...")
    frontend_dir = os.path.join(project_root, "frontend")
    # On Windows, npx is a cmd script so shell=True is needed.
    run_command(
        ["npx", "openapi-typescript", "../schema.yaml", "-o", "src/types/api.d.ts"],
        cwd=frontend_dir,
        shell=(os.name == "nt"),
    )

    print("[3/3] Done!")
    print("SUCCESS: Frontend synchronized with Backend!")


if __name__ == "__main__":
    main()
