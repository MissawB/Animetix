# 🛠️ Design Spec: Animetix Monetization Pivot (Hybrid Model)

**Date:** 2026-05-26  
**Status:** Approved  
**Topic:** Transition from zero-monetization to a Hybrid (Freemium + B2B API) model.

---

## 1. Executive Summary
Animetix is pivoting to a sustainable hybrid monetization model. The strategy focuses on two primary pillars:
- **B2C (End Users):** A classic Freemium model with tiered service quality, quotas, and non-intrusive rewarded advertisements.
- **B2B (Developers):** A pay-as-you-go API access to the RAG 2.0 engine and Knowledge Graph.

The goal is to provide a high-quality free experience while incentivizing power users and professional developers to contribute to the platform's sustainability.

---

## 2. Monetization Tiers (B2C)

### 2.1 Free Tier (Standard)
- **Monetization:** Rewarded Video Ads (provided by external connectors). Watching a video grants a temporary quota boost.
- **Quota:** 30 AI requests per day (reset at midnight).
- **Inference Priority:** Low. Requests enter a "Slow Queue" during high server load (>80% capacity).
- **Model Quality:** Access to "Flash" models (e.g., Llama-3-8B GGUF 4-bit) for cost efficiency and speed.
- **Ads:** Rewarded ads only; no intrusive banners in the main UI flow.

### 2.2 Premium Tier (Pro)
- **Monetization:** Monthly/Annual Subscription (Stripe Integration).
- **Quota:** 500 AI requests per day (effectively unlimited for human usage).
- **Inference Priority:** Instant. Dedicated inference slots using vLLM backends.
- **Model Quality:** Access to "Pro" models (e.g., Llama-3-70B FP16, specialized Vision models).
- **Ads:** 100% Ad-free experience.

---

## 3. Developer API (B2B)
- **Model:** Pay-as-you-go.
- **Pricing:** Billed per 1k tokens or per request (e.g., $0.01 per complex RAG query).
- **Capabilities:** Full access to Knowledge Graph (Neo4j), Semantic Search (PgVector), and Agentic reasoning tools.
- **Infrastructure:** Rate-limited keys managed via a developer dashboard.

---

## 4. Technical Architecture

### 4.1 User Tier Manager (Backend)
- **Layer:** Core Domain / Middleware.
- **Purpose:** Identifies the user's tier on every request and attaches service-level metadata to the context.
- **Persistence:** Stored in the Django User model/profile.

### 4.2 Smart Inference Router (Infrastructure Adapter)
- **Layer:** Adapters (Inference).
- **Mechanism:** Dynamically routes requests to specific backends based on `InferencePriority`.
  - **Premium:** Directed to high-performance vLLM endpoints.
  - **Free:** Directed to local GGUF workers or lower-priority inference pools.

### 4.3 Quota Tracker (Infrastructure)
- **Layer:** Persistence / Cache.
- **Technology:** Redis-backed counters for real-time validation with low latency.
- **Logic:** Decoupled from business logic to ensure it can be bypassed for internal/admin accounts.

### 4.4 API Billing Adapter (Infrastructure)
- **Layer:** Adapters (Persistence/External).
- **Integration:** Stripe Billing or Neon's internal usage tracking to calculate and invoice monthly API usage.

### 4.5 Rewarded Ad Connector (Frontend)
- **Layer:** Frontend Component.
- **Implementation:** React component that interacts with Ad providers (e.g., Google AdMob/IMA SDK) and triggers a backend endpoint to increment the daily quota upon successful video completion.

---

## 5. Success Criteria
- **Conversion:** 2-5% of active users converting to Premium within the first 6 months.
- **Performance:** No more than 50ms overhead for quota validation.
- **Sustainability:** Ad revenue + Premium subs covering 100% of inference costs.
- **API Adoption:** At least 5 active external integrations within the first quarter.

---

## 6. Future Considerations
- **Tiered API:** Moving to Bronze/Silver/Gold tiers if usage patterns become predictable.
- **Marketplace:** Selling custom "Archetype Adapters" for La Forge in a digital store.
