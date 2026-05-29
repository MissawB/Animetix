import os
import sys
import logging
import django
from pathlib import Path

# Setup Django environment
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.append(str(PROJECT_ROOT / "src" / "backend"))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "animetix_project.settings")
django.setup()

from django.db import connection
from django.core.cache import cache
from animetix.containers import get_container

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger("pre-flight")

def check_env_vars():
    logger.info("🔍 Checking Environment Variables...")
    required = ["DATABASE_URL", "REDIS_URL", "HUGGINGFACE_TOKEN", "SECRET_KEY"]
    missing = [v for v in required if not os.getenv(v)]
    if missing:
        logger.error(f"❌ Missing critical variables: {', '.join(missing)}")
        return False
    logger.info("✅ Environment variables OK.")
    return True

def check_postgres():
    logger.info("🐘 Checking PostgreSQL Connection...")
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT version();")
            version = cursor.fetchone()
            logger.info(f"✅ Postgres Connection OK: {version[0]}")
        return True
    except Exception as e:
        logger.error(f"❌ PostgreSQL Connection Failed: {e}")
        return False

def check_redis():
    logger.info("🚀 Checking Redis Cache...")
    try:
        cache.set("preflight_test", "ok", timeout=5)
        if cache.get("preflight_test") == "ok":
            logger.info("✅ Redis Connection OK.")
            return True
        else:
            logger.error("❌ Redis write/read failed.")
            return False
    except Exception as e:
        logger.error(f"❌ Redis Connection Failed: {e}")
        return False

def check_neo4j():
    logger.info("🕸️ Checking Neo4j Knowledge Graph...")
    container = get_container()
    if not container.neo4j_manager:
        logger.error("❌ Neo4j Manager not found in container.")
        return False
    
    status = container.neo4j_manager.check_health()
    if status.get("status") == "online":
        logger.info("✅ Neo4j Connection OK.")
        return True
    else:
        logger.error(f"❌ Neo4j Offline: {status.get('reason')}")
        return False

def check_ai_engines():
    logger.info("🧠 Checking AI Inference Engines...")
    container = get_container()
    status = container.inference_engine.health_check()
    
    if status.get("status") == "online":
        logger.info(f"✅ AI Engine Online. Adapters: {status.get('adapters')}")
        return True
    else:
        logger.error(f"❌ AI Engine Offline or Degraded: {status}")
        return False

def check_dependencies():
    logger.info("📦 Checking critical Python dependencies...")
    try:
        import bleach
        import pydantic
        import yaml
        logger.info("✅ Dependencies (bleach, pydantic, pyyaml) OK.")
        return True
    except ImportError as e:
        logger.error(f"❌ Missing dependency: {e}")
        return False

def run_all():
    print("\n" + "="*40)
    print("🚀 ANIMETIX PRE-FLIGHT CHECK 🚀")
    print("="*40 + "\n")
    
    results = [
        check_env_vars(),
        check_dependencies(),
        check_postgres(),
        check_redis(),
        check_neo4j(),
        check_ai_engines()
    ]
    
    print("\n" + "="*40)
    if all(results):
        print("🟢 SYSTEM READY FOR DEPLOYMENT!")
        sys.exit(0)
    else:
        print("🔴 SYSTEM NOT READY. Please fix errors above.")
        sys.exit(1)

if __name__ == "__main__":
    run_all()
