# 📊 Cost Audit & Economic Strategy - Animetix

This document presents a detailed audit of the operational costs for the **Animetix** platform and defines the sustainability of the economic model based on **Bx** (Berrix tokens).

---

## 1. Artificial Intelligence & Inference (Variable Costs)

Animetix uses a hybrid inference architecture to balance "SOTA" performance and cost-effectiveness. Costs are calculated by the internal `PricingService`.

### 1.1. Large Language Models (LLM)
*Average cost per 1 million tokens (Input + Output).*

| AI Engine | Usage | Cost (USD/1M tokens) |
| :--- | :--- | :--- |
| **GPT-4o / Claude 3 Sonnet** | Complex RAG, VN Scenarios | **$10.00 to $18.00** |
| **Brain API (Custom)** | Neural business logic | **$1.50 to $3.00** |
| **Llama-3-8B / Qwen-2.5** | Standard Chat, Akinetix RL | **~$0.10** (if third-party API) |
| **Local LLM (Ollama)** | Basic Chat, NPC | **$0.00** (Infrastructure cost only) |

### 1.2. Generative Models (Per-unit)
*Cost per single request.*

| Model | Action | Cost (USD/unit) |
| :--- | :--- | :--- |
| **SDXL Turbo** | Image Generation (Forge) | **$0.01** |
| **Coqui XTTS-v2** | Voice Cloning (Voice Lab) | **$0.005** |
| **Manga OCR** | Text Extraction | **$0.00** (Local execution) |

---

## 2. Infrastructure & Cloud (Fixed Costs)

Estimation based on a production deployment on **Google Cloud Platform (GCP)** or a specialized GPU provider (RunPod/Lambda).

| Resource | Service | Est. Monthly Cost | Role |
| :--- | :--- | :--- | :--- |
| **GPU Inference (`animetix-brain`)** | Cloud Run GPU (serverless, on-demand) | **$0 idle → $450-1200 under load** | Inference for Ghost Labs & SLMs |
| **Cloud Run / GKE** | Django Backend | **$40 - $150** | API, Celery Workers, WebSockets |
| **Databases** | Cloud SQL + Neo4j Aura | **$80 - $200** | Relational and Graph persistence |
| **Vector Store** | pgvector (Postgres extension) | **$30 - $60** | RAG Engine (Lore & Semantics) |
| **Cloud Storage** | GCS Buckets | **$15 - $50** | Media assets, manga pages |

**Total Estimated Infrastructure Cost: ~$150 to $1600 / month** (the wide range reflects the GPU service, which is the dominant *variable* — not fixed — cost).

> ⚠️ **Audit note (2026-06-22): GPU cost posture corrected — the brain already scales to zero.**
> The `animetix-brain` GPU service runs on **Cloud Run (serverless)**, deployed by the versioned script [`scripts/deploy/deploy_brain.py`](../../scripts/deploy/deploy_brain.py) (NVIDIA L4, secrets, VPC egress, GCS-FUSE model volume). Cloud Run's default `minInstances=0` means the GPU **already scales to zero → $0 when idle** (cold-start latency on the first request); the earlier "$450-1200 fixed" framing was inaccurate — this cost is load-driven, not a permanent floor.
> The residual gap was that the scaling bounds were *implicit*: `--min-instances`/`--max-instances` were unset, so scale-to-zero was undocumented and `max` defaulted to 100 (uncapped). **Fixed 2026-06-22** by making `--min-instances=0` and `--max-instances=3` explicit in the deploy script (the ceiling is aligned with the `restore_brain_service` default). The GPU cost floor is now auditable from git.

---

## 3. Third-Party Services & Observability

| Service | Monthly Cost | Role |
| :--- | :--- | :--- |
| **Firebase Auth** | Free (standard tier) | Authentication & Security |
| **Sentry / PostHog** | **$50 - $100** | Error monitoring and Product Analytics |
| **Stripe** | 2.9% + $0.30 / trans. | Processing Berrix purchases |

---

## 4. Profitability Analysis: The "Berrix" Model (Minimal Margin)

The **Berrix** (Bx) token system was recalibrated on June 13, 2026, to shift from a profitable model to a **"Break-even" (Social Equilibrium)** model, minimizing margins for the user's benefit.

### 4.1. Cost/Revenue Ratio (Advertising)
*   **Average revenue of a Rewarded Ad (30s):** ~$0.015 to $0.025.
*   **User Credit:** **+250 Bx** (Berrix).
*   **Cost of a standard AI call (5 Bx):** ~$0.00005.
*   **Cost of a Forge Image (50 Bx):** ~$0.0005.

**Observation:** A single video ad now finances approximately 400 to 500 simple AI calls or 5 creative fusions. The generated surplus is used to cover the GPU service usage — which, on serverless Cloud Run GPU, is a *variable* load-driven cost, not a permanent fixed cluster (see §2 audit note).

### 4.2. Cost/Revenue Ratio (Direct Purchase)
*   **Initiate Pack (10,000 Bx for €4.99):**
    *   Net revenue (after Stripe/Apple fees): ~$4.30.
    *   Max service cost (if entirely spent on images): ~$1.00.
    *   **Gross Margin: ~75%** (Reinvested in fixed infrastructure costs).

---

## 5. Recommendations for Optimization

1.  **Prioritize Local:** Systematically migrate chat tasks to **SLMs (Small Language Models)** like Qwen-2.5-1.5B hosted on our own instances to reduce reliance on expensive APIs (OpenAI/Anthropic).
2.  **Spot Instances:** Use GPU "Spot" instances (preemptible) for Celery workers on the Forge to reduce server costs by 60-80%.
3.  **Semantic Caching:** Implement a semantic cache for RAG to avoid paying twice for identical queries from different users.
4.  **Image Compression:** Use WebP aggressively to reduce bandwidth egress and GCS storage costs.

---
*Last audit update: June 22, 2026 (GPU cost posture corrected: Cloud Run serverless, not fixed Compute Engine).*
