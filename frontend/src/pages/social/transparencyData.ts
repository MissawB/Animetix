// Comparatif curé : notre modèle de base (Qwen3.5-9B, servi en local et
// fine-tuné DPO en continu → "Champion") face aux meilleurs LLM open source
// du marché. Liste volontairement locale à cette page — le service SOTA
// backend alimente d'autres écrans (admin) et n'est pas modifié.
export interface ComparisonModel {
  model_id: string;
  provider: string;
  params: string;
  license: string;
  elo_score: number;
  mmlu_score: number;
  isOurs?: boolean;
}

export const MODEL_COMPARISON: ComparisonModel[] = [
  {
    model_id: 'Qwen/Qwen3.5-9B',
    provider: 'Animetix · base Qwen (Alibaba)',
    params: '9B',
    license: 'Apache 2.0',
    elo_score: 1248,
    mmlu_score: 79.8,
    isOurs: true,
  },
  {
    model_id: 'deepseek-ai/DeepSeek-V3.2',
    provider: 'DeepSeek',
    params: '671B MoE',
    license: 'MIT',
    elo_score: 1445,
    mmlu_score: 90.8,
  },
  {
    model_id: 'Qwen/Qwen3-235B-A22B',
    provider: 'Alibaba',
    params: '235B MoE',
    license: 'Apache 2.0',
    elo_score: 1438,
    mmlu_score: 89.9,
  },
  {
    model_id: 'moonshotai/Kimi-K2',
    provider: 'Moonshot AI',
    params: '1T MoE',
    license: 'MIT modifiée',
    elo_score: 1432,
    mmlu_score: 89.5,
  },
  {
    model_id: 'meta-llama/Llama-4-Maverick',
    provider: 'Meta',
    params: '400B MoE',
    license: 'Llama 4',
    elo_score: 1417,
    mmlu_score: 88.6,
  },
];
