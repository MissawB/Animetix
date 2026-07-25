import { apiClient } from '../../../utils/apiClient';

export const mlopsService = {
  getEvalFailures: async () => {
    return apiClient('/api/v1/mlops/eval/failures/');
  },

  runDSPyOptimizer: async (payload?: Record<string, unknown>) => {
    return apiClient('/api/v1/mlops/dspy/optimizer/', {
      method: 'POST',
      body: payload ? JSON.stringify(payload) : undefined,
    });
  },

  getSafetyEvents: async () => {
    return apiClient('/api/v1/mlops/safety/events/');
  },

  getSotaBenchmarks: async () => {
    return apiClient('/api/v1/mlops/sota/benchmarks/');
  },
};
