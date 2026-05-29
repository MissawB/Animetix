import os
import polib
from pathlib import Path

def compile_translations():
    """
    Compiles .po files to .mo files using polib.
    Fallback for systems without GNU gettext installed.
    """
    # Project structure: scripts/compile_translations.py
    # Locale folder is at: backend/api/locale/
    script_dir = Path(__file__).resolve().parent
    project_root = script_dir.parent
    locale_dir = project_root / "src" / "backend" / "locale"

    if not locale_dir.exists():
        print(f"❌ Locale directory not found at {locale_dir}")
        return

    print(f"🔍 Searching for .po files in {locale_dir}...")
    
    po_files = list(locale_dir.rglob("*.po"))
    
    if not po_files:
        print("⚠️ No .po files found.")
        return

    for po_path in po_files:
        mo_path = po_path.with_suffix(".mo")
        print(f"⚙️ Compiling {po_path.relative_to(project_root)} -> {mo_path.relative_to(project_root)}")
        
        try:
            po = polib.pofile(str(po_path))
            po.save_as_mofile(str(mo_path))
            print(f"✅ Success!")
        except Exception as e:
            print(f"❌ Error compiling {po_path.name}: {e}")

if __name__ == "__main__":
    compile_translations()
