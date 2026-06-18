import argparse
from animetix.containers import get_container


def run_self_play_session(limit: int = 5):
    """
    Lance une session automatique de Self-Play Debating pour générer
    des données de raisonnement complexe pour le DPO/Fine-tuning.
    """
    print("⚔️ Starting Self-Play Debating Session...")

    container = get_container()
    debate_service = container.self_play_debate_service()
    catalog = container.repository().load_catalog("Anime")

    if not catalog:
        print("❌ Catalog not found.")
        return

    sample_items = catalog["db"][:limit]
    topics = [
        "Le développement du personnage principal est mal rythmé.",
        "La fin de l'œuvre détruit tout le message précédent.",
        "Les thèmes philosophiques sont superficiels et prétentieux.",
    ]

    import random  # noqa: E402

    success_count = 0

    for item in sample_items:
        title = item.get("title", "Inconnu")
        topic = random.choice(topics)

        try:
            record = debate_service.run_debate(target_media=title, topic=topic)
            if record:
                success_count += 1
        except Exception as e:
            print(f"❌ Debate failed for {title}: {e}")

    print("\n" + "=" * 40)
    print(f"🏁 Session completed. {success_count}/{limit} debates recorded.")
    print(f"💾 Check '{debate_service.dataset_path}' for training data.")
    print("=" * 40)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=3)
    args = parser.parse_args()

    run_self_play_session(limit=args.limit)
