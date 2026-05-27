import os
import django
import logging

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'animetix_project.settings')
django.setup()

from backend.animetix.containers import get_container

def run_test_battle(char_a, char_b):
    container = get_container()
    vs_service = container.vs_battle_service()
    
    print(f"\n⚔️  DÉBUT DU DUEL : {char_a} VS {char_b}")
    print("-" * 50)
    
    try:
        result = vs_service.run_battle(char_a, char_b)
        
        print(f"\n📊 STATS RÉCUPÉRÉES :")
        print(f"[{result.character_a.name}] Tier: {result.character_a.stats.tier} (Score: {result.character_a.stats.tier_value})")
        print(f"[{result.character_b.name}] Tier: {result.character_b.stats.tier} (Score: {result.character_b.stats.tier_value})")
        
        print("\n🎤 DÉBAT DES AVOCATS :")
        for turn in result.debate_history:
            if turn.agent != "Judge":
                print(f"\n[{turn.agent}] : {turn.content[:300]}...")
        
        print("\n⚖️  VERDICT DU JUGE :")
        print(result.verdict_summary)
        print(f"\n🏆 VAINQUEUR : {result.winner}")
        
    except Exception as e:
        print(f"❌ Erreur lors du combat : {e}")

if __name__ == "__main__":
    # Test avec un perso wiki et un perso IA
    run_test_battle("Levi Ackerman", "Thorfinn Karlsefni")
