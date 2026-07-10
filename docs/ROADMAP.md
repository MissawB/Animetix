# 🗺️ Global AI Roadmap (OPERATIONAL)

This document formalizes the strategic planning and technical architecture of semantic, cognitive, immersive, and evolving enhancements for the **Animetix** platform.

---

## 📅 Integration Timeline (Last update: July 10, 2026)

The entire cognitive and multimodal architecture is now operational and live at **animetix.xyz**. The project is deep into the hardening and technical-debt paydown phase.

```mermaid
gantt
    title Animetix Development Timeline 2026
    dateFormat  YYYY-MM-DD
    
    section AI Foundations
    Phase A: Research & RAG                  :done, a1, 2026-06-01, 2026-06-05
    Phase B: Inference & Speed              :done, b1, 2026-06-05, 2026-06-10
    Phase C: Learning & DPO                  :done, c1, 2026-06-10, 2026-06-12
    Phase D: Multimodal Immersion            :done, d1, 2026-06-12, 2026-06-13
    
    section Convergence & Cloud
    Phase M: Rewarded Economy (Berrix)       :done, m1, 2026-06-13, 2026-06-14
    Cloud Integration (GCIP, Cloud Run)      :done, c2, 2026-06-10, 2026-06-15
    
    section Robustness & Security
    Phase S: Hardening & MLOps (XAI/Drift/Budgets):done, s1, 2026-06-14, 2026-07-07
    Debt Paydown (namespace, god-files, DI)  :done, s3, 2026-07-05, 2026-07-10
    Maintenance Mode & Error Pages           :done, s4, 2026-07-09, 2026-07-10
    Accessibility Audit (WCAG)               :active, s2, 2026-07-07, 2026-07-15
    
    section Future & Expansion
    Ghost Labs Stabilization                 :f1, 2026-07-15, 2026-08-01
    Multi-Region Deployment                  :f2, 2026-08-01, 2026-08-15
```

---

## 🛠️ Status of Technical Specifications

#### Phases A-D: Core Foundations (COMPLETED)
*   **Hybrid RAG & Graphs:** Integration of `HierarchicalGraphRAGService` (Neo4j + Vertex AI).
*   **Unified Inference:** Native support for Ollama, OpenAI, and Gemini via `InferencePort`.
*   **DPO Learning:** Autonomous feedback loop for prompt optimization.
*   **Vision & 3D:** Video-LLaVA indexing and cinematic volumetric reconstruction operational.

#### Phases E-L: Advanced Cognition (COMPLETED - Integrated)
*   **Tree of Thoughts (ToT):** MCTS for complex queries.
*   **Neuro-Symbolic Profiling:** Z3 solver for preference deduction.
*   **Hebbian Plasticity:** Real-time evolution of user semantic weights.
*   **Multiverse Synthesis:** Autonomous generator of fictional worlds with HITL validation.

#### Phase M & Cloud: Economy & Infrastructure (COMPLETED, then simplified)
*   **Berrix Economy:** Replacement of Premium tier with a rewarded ad model; the platform is 100% free.
*   **Payments removed (2026-07-07):** the entire Stripe stack (checkout, metered billing, webhooks) was deleted — Berrix cannot be bought, and the developer API "pro" tier is granted manually for free.
*   **SOTA Google Cloud:** GCIP (Auth) and Cloud Run in production; **pgvector (Neon)** is the production vector store (the Vertex Vector Search wrapper remains optional). The AlloyDB AI Text-to-SQL surface was removed as dead code (2026-07-05).

#### Phase S: Robustness, Security, MLOps & Billing (COMPLETED)
*   **Network Security:** Direct VPC Egress and Cloud Armor WAF rules configured.
*   **Embedding & Archetype Drift:** Wasserstein distance query embedding drift checking and alerting (`generate_drift_baselines`).
*   **Explainable AI (XAI):** `XaiDiagnosticService` logprob confidence profiling, attention heatmaps, and logit lens projections.
*   **Cost Containment & Webhook**: Automatic billing webhook executing graceful shutdowns of GPU inference services once budget caps are reached.

#### Debt Paydown Sprint — July 5-10, 2026 (COMPLETED)
*   **Import namespace unified** on the bare root with a 3-layer regression tripwire.
*   **Secret hygiene closed:** `.env` can no longer reach any image; pre-exclusion registry images purged; all prod secrets mounted from Secret Manager.
*   **Prod WebSockets repaired** (`channels-redis`) and verified live (101 handshake).
*   **God-files decomposed:** `api/labs.py` and `api/core.py` split into domain packages.
*   **Service locator eradicated:** the whole view layer is constructor-injected (`dependency_injector`), `ProviderDelegate` deleted, 16 latent flat-access crashes repaired.
*   **List-endpoint N+1s fixed** with query-count regression locks; broken public-profile and authenticated `/config/` endpoints repaired (`Profile.rank`).
*   **Maintenance mode** shipped: `SiteConfiguration` solo model, fail-open middleware, frontend gate and restyled error pages.
*   Full details per session in [HISTORY.md](HISTORY.md).

---

## 📜 Revision Notes

**Global Status:**
- The AI architecture is **100% stabilized** and complies with the July 2026 specifications.
- Hardening of security and MLOps constraints was finalized with the deployment of declarative deployment manifests, automated drift checks, and secure billing push subscriptions.

**Immediate Priorities:**
- Finalize the accessibility audit (WCAG) via Playwright.
- Revoke the two dead keys still present in the local `.env` (Tripo3D / Mapbox dashboards).
- Sweep the runtime paths for silent `except Exception` handlers; purge the 49 pre-squash migrations once prod has transitioned.
- Automate weekly security compliance reports.
