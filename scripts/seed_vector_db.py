import os
import sys
import importlib.util

# Détection robuste de la racine du projet
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PIPELINE_DIR = os.path.join(BASE_DIR, 'pipeline')

# Ajout des chemins nécessaires au PYTHONPATH
if BASE_DIR not in sys.path:
    sys.path.append(BASE_DIR)
if PIPELINE_DIR not in sys.path:
    sys.path.append(PIPELINE_DIR)

def load_module_from_path(module_name, file_path):
    """Charge dynamiquement un module à partir d'un chemin de fichier."""
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module

def run_task(name, module, func_name="run_vectorization"):
    """Exécute une tâche de vectorisation de manière sécurisée."""
    print(f"\n--- 🚀 {name.upper()} VECTORIZATION ---")
    try:
        func = getattr(module, func_name, None)
        if func:
            func()
        else:
            print(f"⚠️ Function '{func_name}' not found in module {name}.")
    except Exception as e:
        print(f"❌ Error during {name} vectorization: {e}")

def run_all_vectorizations():
    """
    Exécute toutes les tâches de vectorisation pour alimenter ChromaDB et Neo4j.
    """
    print("🌟 Starting Global Vectorization & Seeding Process...")

    # 1. Modules standards (Anime, Manga, Characters)
    try:
        from anime import vectorize_anime
        run_task("Anime", vectorize_anime)
    except ImportError as e:
        print(f"⚠️ Could not load Anime module: {e}")

    try:
        from manga import vectorize_manga
        run_task("Manga", vectorize_manga)
    except ImportError as e:
        print(f"⚠️ Could not load Manga module: {e}")

    try:
        from characters import vectorize_characters
        run_task("Characters", vectorize_characters)
    except ImportError as e:
        print(f"⚠️ Could not load Characters module: {e}")

    # 2. Modules avec chiffres (Games, Movies, Actors)
    tasks_with_paths = [
        ("Games", os.path.join(PIPELINE_DIR, "games", "5_vectorize_games.py"), "main"),
        ("Movies", os.path.join(PIPELINE_DIR, "movies", "5_vectorize_movies.py"), "main"),
        ("Actors", os.path.join(PIPELINE_DIR, "actors", "5_vectorize_actors.py"), "main")
    ]

    for name, path, func_name in tasks_with_paths:
        if os.path.exists(path):
            try:
                module = load_module_from_path(f"vectorize_{name.lower()}", path)
                run_task(name, module, func_name)
            except Exception as e:
                print(f"⚠️ Could not load or run {name} module from {path}: {e}")
        else:
            print(f"ℹ️ {name} vectorization script not found at {path}")

    print("\n✨ All vectorization processes finished.")

if __name__ == "__main__":
    run_all_vectorizations()
