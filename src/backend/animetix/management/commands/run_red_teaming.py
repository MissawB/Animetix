from django.core.management.base import BaseCommand
from animetix.containers import get_container
import json

class Command(BaseCommand):
    help = 'Lance une session de Red-Teaming automatique pour identifier les failles du RAG.'

    def add_arguments(self, parser):
        parser.add_argument('--limit', type=int, default=5, help='Nombre d\'œuvres à tester')

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('🚀 Starting Red-Teaming Session...'))
        
        container = get_container()
        red_teamer = container.red_teaming_agent()
        
        # 1. Sélection d'un échantillon d'œuvres
        catalog_service = container.catalog_service()
        catalog = catalog_service.load_data('Anime')
        if not catalog:
            self.stdout.write(self.style.ERROR('Catalogue non trouvé.'))
            return
            
        sample_items = catalog['db'][:options['limit']]
        
        results = []
        
        for item in sample_items:
            self.stdout.write(f"🧐 Attacking: {item['title']}...")
            
            # 2. Génération de requêtes adverses
            queries = red_teamer.generate_adversarial_queries(item)
            
            for q in queries:
                self.stdout.write(f"  🔥 Query: {q}")
                
                # 3. Exécution via l'IA normale (Agentic RAG)
                agentic_rag = container.agentic_rag()
                response = agentic_rag.plan_and_solve(q, 'Anime')
                
                # 4. Évaluation de la vulnérabilité
                eval_res = red_teamer.evaluate_vulnerability(
                    query=q, 
                    response=response, 
                    ground_truth=item['description']
                )
                
                results.append({
                    "item": item['title'],
                    "query": q,
                    "response": response,
                    "vulnerable": eval_res['is_vulnerable'],
                    "analysis": eval_res['analysis']
                })
                
                if eval_res['is_vulnerable']:
                    self.stdout.write(self.style.WARNING(f"  ⚠️ Vulnerability Found: {eval_res['analysis']}"))

        # 5. Rapport final
        output_path = "data/mlops/red_teaming_report.json"
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2)
            
        total_vulns = sum(1 for r in results if r['vulnerable'])
        self.stdout.write(self.style.SUCCESS(f"🏁 Red-Teaming finished. Found {total_vulns} vulnerabilities."))
        self.stdout.write(f"💾 Report saved to {output_path}")
