import os
import sys
import django
import json
import time
import pandas as pd
from datetime import datetime

# 1. Setup environment
base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(os.path.join(base_dir, "src"))
sys.path.append(os.path.join(base_dir, "src", "backend"))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'animetix_project.settings')
django.setup()

from django.conf import settings
print(f"📌 Using Database: {settings.DATABASES['default']['NAME']}")

from animetix.containers import get_container
from ragas import evaluate
from ragas.metrics import faithfulness, answer_relevancy, context_recall
from ragas.embeddings import LangchainEmbeddingsWrapper
from datasets import Dataset
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
import wandb

def run_targeted_quality_benchmark():
    print("🚀 Starting Targeted Quality Benchmark (Faithfulness & Relational Accuracy)...")
    print("🤖 Version: Animetix Ultra (SOTA 2026 + Deep Reflection)")
    
    # 2. Setup Container and RAG
    container = get_container()
    rag = container.agentic_rag
    
    # 3. Load and Filter Gold Set
    gold_path = os.path.join(base_dir, 'data', 'mlops', 'gold_dataset.json')
    with open(gold_path, 'r', encoding='utf-8') as f:
        gold_data = json.load(f)
    
    # Targeting Relational Accuracy (graph, cross-media) and general quality (thematic)
    target_types = ['graph', 'cross-media', 'thematic']
    eval_set = [e for e in gold_data if e.get('query_type') in target_types]
    
    # Add some standard/visual for faithfulness baseline
    other_set = [e for e in gold_data if e.get('query_type') not in target_types][:5]
    eval_set = eval_set + other_set
    
    print(f"📊 Benchmark Set: {len(eval_set)} queries selected.")
    
    # 4. W&B Initialization
    wandb.init(
        project="animetix-official-benchmarks",
        name=f"targeted-quality-{datetime.now().strftime('%Y%m%d-%H%M')}",
        config={
            "architecture": "Deep Reflection State Machine",
            "llm": "Qwen3-4B-Instruct",
            "vision": "SigLIP-2",
            "states": ["PLAN", "RESEARCH", "SYNTHESIZE", "JUDGE"]
        }
    )
    
    # 5. Generate Answers
    results_data = []
    for i, entry in enumerate(eval_set):
        q = entry['query']
        q_type = entry.get('query_type', 'standard')
        print(f"[{i+1}/{len(eval_set)}] [{q_type}] Processing: {q[:60]}...")
        
        start = time.time()
        answer = ""
        # We'll also track state transitions for logging
        states_visited = []
        
        try:
            for event in rag.plan_and_solve_stream(q, "Anime"):
                if event['type'] == 'token':
                    answer += event['content']
                elif event['type'] == 'thought' and "[State Machine]" in event['content']:
                    # Extract state name
                    state = event['content'].split("État: ")[-1]
                    states_visited.append(state)
            
            # Context for RAGAS (re-retrieval for benchmark consistency)
            search_results = container.rag_service.hybrid_search(q, "Anime")
            contexts = [r.get('description', '') for r in search_results]
            if not contexts: contexts = ["No context found"]
            
        except Exception as e:
            print(f"   ⚠️ Error: {e}")
            answer = "ERROR"
            contexts = ["ERROR"]
            
        latency = time.time() - start
        
        results_data.append({
            "question": q,
            "answer": answer,
            "contexts": contexts,
            "ground_truth": entry.get('ground_truth', entry.get('expected_title', '')),
            "query_type": q_type,
            "latency": latency,
            "num_iterations": len(states_visited) // 4 + 1, # Approx
            "states": ", ".join(states_visited)
        })
        
    # 6. RAGAS Evaluation
    print("\n⚖️ Calculating Faithfulness & Accuracy via Ragas...")
    df = pd.DataFrame(results_data)
    dataset = Dataset.from_pandas(df)
    
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("❌ GEMINI_API_KEY not found. Logging raw answers only.")
        wandb.log({"answers": wandb.Table(dataframe=df)})
        wandb.finish()
        return

    eval_llm = ChatGoogleGenerativeAI(model="gemini-3.1-flash-lite-preview", google_api_key=api_key)
    eval_embeddings = GoogleGenerativeAIEmbeddings(model="models/text-embedding-004", google_api_key=api_key)
    
    try:
        all_results_df = []
        batch_size = 5
        total_batches = (len(dataset) + batch_size - 1) // batch_size
        
        for i in range(0, len(dataset), batch_size):
            print(f"   ⏳ Evaluating batch {i//batch_size + 1}/{total_batches} (waiting to respect rate limits)...")
            batch_dataset = dataset.select(range(i, min(i + batch_size, len(dataset))))
            
            try:
                eval_result = evaluate(
                    batch_dataset,
                    metrics=[faithfulness, answer_relevancy, context_recall],
                    llm=eval_llm,
                    embeddings=LangchainEmbeddingsWrapper(eval_embeddings)
                )
                all_results_df.append(eval_result.to_pandas())
            except Exception as batch_e:
                print(f"   ⚠️ Batch {i//batch_size + 1} failed: {batch_e}. Skipping to next.")
            
            time.sleep(8) # Pause to prevent 429 RateLimit or Timeout errors
            
        if not all_results_df:
            raise ValueError("All batches failed during Ragas evaluation.")
            
        results_df = pd.concat(all_results_df, ignore_index=True)
        # Merge back metadata
        results_df['query_type'] = df['query_type']
        
        # Log to W&B
        wandb.log({"detailed_quality_results": wandb.Table(dataframe=results_df)})
        
        summary = results_df.groupby('query_type').mean(numeric_only=True)
        print("\n📈 QUALITY BENCHMARK SUMMARY")
        print(summary[['faithfulness', 'answer_relevancy', 'context_recall']])
        
        # Relational Accuracy is specific to graph/cross-media
        relational_acc = results_df[results_df['query_type'].isin(['graph', 'cross-media'])]['faithfulness'].mean()
        print(f"\n🎯 TARGET: Relational Accuracy (Faithfulness on Graph): {relational_acc:.2f}")
        wandb.log({"relational_accuracy_score": relational_acc})
        
    except Exception as e:
        print(f"❌ Ragas Evaluation failed: {e}")
        wandb.log({"raw_data": wandb.Table(dataframe=df)})

    wandb.finish()
    print("✅ Benchmark complete.")

if __name__ == "__main__":
    run_targeted_quality_benchmark()
