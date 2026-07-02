import subprocess
import sys


def setup_e2e():
    """Installs Playwright and its browser dependencies."""
    print("🚀 Installing Playwright browsers...")
    try:
        subprocess.run(
            [sys.executable, "-m", "playwright", "install", "--with-deps", "chromium"],
            check=True,
        )
        print("✅ Playwright installation successful.")
    except subprocess.CalledProcessError as e:
        print(f"❌ Playwright installation failed: {e}")
    except FileNotFoundError:
        print(
            "❌ Playwright module not found. Please run 'pip install -r requirements.txt' first."
        )


if __name__ == "__main__":
    setup_e2e()
