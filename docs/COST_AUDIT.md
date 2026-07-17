# 📊 Cost Audit & Economic Strategy - Animetix

This document presents a detailed audit of the operational costs for the **Animetix** platform and defines the sustainability of the economic model based on **Bx** (Berrix tokens).

---

## 1. Artificial Intelligence & Inference (Variable Costs)

Animetix uses a hybrid inference architecture to balance "SOTA" performance and cost-effectiveness. Costs are calculated by the internal `PricingService`.

### 1.1. Large Language Models (LLM)
*Average cost per 1 million tokens (Input + Output).*

| AI Engine | Usage | Cost (USD/1M tokens) |
| :--- | :--- | :--- |
| **Gemini 3.5 Flash** (`google_genai`) | Complex RAG, VN scenarios, S2S Live | **Flash tier (~$0.15 to $0.60, est.)** |
| **Brain API (Custom)** | Neural business logic (`brain-api`) | **$1.00 to $2.00** |
| **Qwen3.5 (4B / 8B)** | Standard Chat, Akinetix RL (if hosted API) | **~$0.10 to $0.15** |
| **Local LLM (Ollama, `qwen3.5`)** | Basic Chat, NPC | **$0.00** (Infrastructure cost only) |

> ⚠️ **Audit note (2026-07-17): the pricing registry is out of sync with the live chain.** The production inference chain is `[brain_api, google_genai]` ([`containers/inference.py`](../backend/api/animetix/containers/inference.py)) — the brain, then **Gemini** — never OpenAI/Anthropic. Yet [`PricingService`](../backend/core/domain/services/pricing_service.py) still carries `gpt-4o` / `gpt-3.5-turbo` / `claude-3-sonnet` entries (never invoked in prod) and has **no `gemini-*` entry**, so live Gemini calls fall through to the `0.0` unknown-engine fallback and register as free. Separate fix (restores real Bx cost attribution): add the `gemini-3.5-flash` / `gemini-live-2.5-flash-native-audio` ids to the registry and drop the dead OpenAI/Anthropic rows.

### 1.2. Generative Models (Per-unit)
*Cost per single request.*

| Model | Action | Cost (USD/unit) |
| :--- | :--- | :--- |
| **FLUX.1-schnell** | Image Generation (Forge) | **$0.03** |
| **SDXL Turbo** (legacy) | Image Generation (fast) | **$0.01** |
| **Coqui XTTS-v2** | Voice Cloning + S2S TTS | **$0.005** |
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
> The `animetix-brain` GPU service runs on **Cloud Run (serverless)**, deployed by the versioned script [`scripts/deploy/gcp/deploy_brain.py`](../scripts/deploy/gcp/deploy_brain.py) (NVIDIA L4, secrets, VPC egress, GCS-FUSE model volume). Cloud Run's default `minInstances=0` means the GPU **already scales to zero → $0 when idle** (cold-start latency on the first request); the earlier "$450-1200 fixed" framing was inaccurate — this cost is load-driven, not a permanent floor.
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

> **Margin model (2026-06-23): guaranteed by construction.** All Bx economics
> derive from one source of truth, `backend/core/domain/services/berrix_economy.py`:
> a net Bx value (`BX_PRICE_USD_NET ≈ $0.00043`) and a configurable
> `TARGET_MARGIN` (default 10%). Feature prices (`FEATURE_BX_COSTS`) are held at
> or above `bx_cost_for_usd()` — a floor test enforces it. Rewarded ads grant
> `ad_reward_bx()` (≈ 41 Bx, down from 250) so ad-funded Bx keep the margin;
> passive mining (10 Bx) is an explicit, capped loss-leader. Packs are sold from
> a server-authoritative catalog at the canonical rate.

The **Berrix** (Bx) token system was recalibrated on June 13, 2026, to shift from a profitable model to a **"Break-even" (Social Equilibrium)** model, minimizing margins for the user's benefit.

### 4.1. Cost/Revenue Ratio (Advertising)
*   **Average revenue of a Rewarded Ad (30s):** ~$0.015 to $0.025.
*   **User Credit:** **+~41 Bx** (calibrated for 10% margin).
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

1.  **Prioritize Local:** Systematically migrate chat tasks to **SLMs (Small Language Models)** like Qwen3.5-4B hosted on our own instances to reduce reliance on the paid **Gemini** API.
2.  **Spot Instances:** Use GPU "Spot" instances (preemptible) for Celery workers on the Forge to reduce server costs by 60-80%.
3.  **Semantic Caching:** Implement a semantic cache for RAG to avoid paying twice for identical queries from different users.
4.  **Image Compression:** Use WebP aggressively to reduce bandwidth egress and GCS storage costs.

---
*Last audit update: July 17, 2026 (model tiers refreshed to the live chain — Gemini 3.5 Flash + Qwen3.5 + brain-api; flagged PricingService gap: no gemini entry, dead OpenAI/Anthropic rows; fixed deploy_brain.py path).*
