import glob
import json
import os


def merge_dicts(dict1, dict2):
    for k, v in dict2.items():
        if k in dict1:
            if isinstance(dict1[k], dict) and isinstance(v, dict):
                merge_dicts(dict1[k], v)
            elif dict1[k] != v:
                print(
                    f"[Warning] Conflict on key '{k}' ('{dict1[k]}' vs '{v}'). Keeping existing value."
                )
        else:
            dict1[k] = v


def sort_dict(d):
    return {k: sort_dict(v) if isinstance(v, dict) else v for k, v in sorted(d.items())}


def main():
    root_dir = os.path.dirname(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    )
    fragments_dir = os.path.join(root_dir, "frontend", "src", "i18n", "fragments")
    locales_dir = os.path.join(root_dir, "frontend", "public", "locales")

    for lng in ["en", "fr"]:
        main_file = os.path.join(locales_dir, lng, "translation.json")
        if not os.path.exists(main_file):
            print(f"[Error] Main file not found: {main_file}")
            continue

        with open(main_file, "r", encoding="utf-8") as f:
            try:
                main_data = json.load(f)
            except Exception as e:
                print(f"[Error] Failed to parse {main_file}: {e}")
                continue

        frag_pattern = os.path.join(fragments_dir, lng, "*.json")
        fragments = glob.glob(frag_pattern)

        if not fragments:
            print(f"[Info] No fragments found for language: {lng}")
            continue

        for frag_path in fragments:
            print(f"[Merge] Merging fragment: {frag_path}")
            with open(frag_path, "r", encoding="utf-8") as f:
                try:
                    frag_data = json.load(f)
                except Exception as e:
                    print(f"[Error] Failed to parse {frag_path}: {e}")
                    continue
            merge_dicts(main_data, frag_data)

        # Sort and write back
        sorted_data = sort_dict(main_data)
        with open(main_file, "w", encoding="utf-8") as f:
            json.dump(sorted_data, f, ensure_ascii=False, indent=2)
        print(f"[Success] Main translation file updated: {main_file}")

        # Delete fragments
        for frag_path in fragments:
            try:
                os.remove(frag_path)
                print(f"[Delete] Deleted fragment: {frag_path}")
            except Exception as e:
                print(f"[Error] Failed to delete fragment {frag_path}: {e}")


if __name__ == "__main__":
    main()
