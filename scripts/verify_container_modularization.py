import sys
import os

# Add src to path
sys.path.append(os.path.abspath("backend/api"))

from animetix.containers import get_container  # noqa: E402


def verify():
    print("Attempting to get container...")
    try:
        container = get_container()
        print("✅ get_container() called successfully.")

        print("Checking infrastructure...")
        pm = container.infrastructure.prompt_manager()
        print(f"✅ PromptManager: {pm}")

        print("Checking persistence...")
        repo = container.persistence.repository()
        print(f"✅ Repository: {repo}")

        print("Checking inference...")
        engine = container.inference.inference_engine()
        print(f"✅ InferenceEngine: {engine}")

        print("Checking agentic...")
        rag = container.agentic.agentic_rag()
        print(f"✅ AgenticRAG: {rag}")

        print("Checking core services...")
        game_service = container.core.game_service()
        print(f"✅ GameService: {game_service}")

        print("\n🚀 All modular containers verified successfully!")

    except Exception as e:
        print(f"❌ Verification failed: {e}")
        import traceback  # noqa: E402

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    verify()
