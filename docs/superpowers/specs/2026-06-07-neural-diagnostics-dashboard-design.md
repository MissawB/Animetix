# Design Specification: Neural Diagnostics Dashboard

Interactive dashboard for real-time visualization of LLM interpretability metrics, including per-token entropy and layer-wise activation convergence (Logit Lens).

## 1. Vision & Purpose
To demystify the "black box" of LLM generations by providing researchers and advanced users with high-resolution diagnostic data. The dashboard identifies tokens of high uncertainty and visualizes the internal decision-making process of the model across its transformer layers.

## 2. User Interface (SPA - React)

### Layout: Neural Inspection Unit
- **Header:** Session ID, Model ID (e.g., Llama-3-8B), and a "Settings" toggle for advanced XAI parameters.
- **Inference Section (Top):**
  - Prompt textarea with a high-contrast "RUN DIAGNOSTIC" button.
  - Global metrics panel: Gauge charts for Average Entropy and Normalized Confidence.
- **Entropy Visualizer (Middle):**
  - Dynamic bar chart using `Framer Motion` or `Recharts`.
  - X-axis: Generated tokens.
  - Y-axis: Entropy value (bits).
  - Color coding: Green (Low entropy/Safe), Yellow (Moderate), Red (High entropy/Uncertain).
- **Logit Lens Heatmap (Bottom):**
  - A grid-based visualization showing layer-wise convergence.
  - Rows: Transformer Layers (1 to N).
  - Columns: Top 10 most influential tokens.
  - Cell Value: Probability/Logit strength.
  - Color scale: Dark (Low activation) to bright Cyan/Green (High activation).

## 3. Technical Architecture

### Frontend
- **Page:** `frontend/src/pages/labs/NeuralDiagnosticsPage.tsx`.
- **Route:** `/lab/diagnostics/`.
- **Components:**
  - `EntropyBarChart.tsx`: Specialized chart for per-token uncertainty.
  - `LogitLensHeatmap.tsx`: High-performance grid renderer (Canvas or optimized DOM).
- **State Management:** `useNeuralDiagnostics` hook.

### Backend (Django + XAI Service)
- **Endpoint:** `POST /api/v1/labs/diagnostics/`.
- **Logic:**
  1. Trigger inference with `include_logprobs=True`.
  2. Call `XaiDiagnosticService.get_diagnostics`.
  3. Format entropy from `TokenLogProb`.
  4. Generate simulated Logit Lens trajectory if native hidden activations are unavailable (using inverse Gaussian noise aligned with final logprobs).
- **Service:** `XaiDiagnosticService` in `backend/core/domain/services/xai_service.py`.

## 4. Success Criteria
- [ ] User can see a real-time bar chart updating as tokens are generated (or post-generation).
- [ ] High-entropy tokens are visually highlighted in red.
- [ ] Heatmap correctly displays the progression of token confidence across layers.
- [ ] Exportable diagnostic report (JSON).

## 5. Security & Resource Management
- **Throttle:** Limited to 5 diagnostic runs per minute due to high compute/data overhead.
- **Admin Only (Optional):** Consider restricting this dashboard to "Expert" or "Admin" roles if GPU costs scale too high.

## 6. Self-Review Check
1. **Placeholder scan:** Simulation strategy for Logit Lens is defined as a fallback.
2. **Internal consistency:** Aligned with the "Heatmap" choice from brainstorming.
3. **Scope check:** Focused on Diagnostics, avoiding overlap with general chat.
4. **Ambiguity check:** Clarified that entropy is derived from logprobs.
