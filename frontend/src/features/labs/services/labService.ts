import { apiClient } from '../../../utils/apiClient';
import { VideoSegment, OpenDataset, AIFeedback } from '../../../types';

export const labService = {
  getLatent: async () => apiClient('/api/v1/lab/latent/'),
  getManga: async () => apiClient('/api/v1/lab/manga/'),
  getSpatial: async () => apiClient('/api/v1/lab/spatial/'),
  runDiagnostics: async (prompt: string) =>
    apiClient('/api/v1/labs/diagnostics/', {
      method: 'POST',
      body: JSON.stringify({ prompt }),
    }),

  cloneVoice: async (
    text: string,
    audioFile: File,
    pitch: number,
  ): Promise<{ audio_data: string }> => {
    const formData = new FormData();
    formData.append('target_text', text);
    formData.append('reference_audio', audioFile);
    formData.append('pitch', pitch.toString());

    return apiClient('/api/v1/labs/voice-cloning/', {
      method: 'POST',
      body: formData,
      isFormData: true,
    });
  },

  searchVideoSegments: async (
    query: string,
  ): Promise<{ status: string; results: VideoSegment[] }> => {
    return apiClient(`/api/v1/labs/video/search/?q=${encodeURIComponent(query)}`);
  },

  getOpenDatasets: async (): Promise<{ status: string; datasets: OpenDataset[] }> => {
    return apiClient('/api/v1/mlops/open-data/');
  },

  downloadDataset: async (datasetId: string, filename: string): Promise<void> => {
    const blob: Blob = await apiClient(`/api/v1/mlops/open-data/download/${datasetId}/`, {
      responseType: 'blob',
    });

    const downloadUrl = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = downloadUrl;
    link.setAttribute('download', filename);
    document.body.appendChild(link);
    link.click();
    link.parentNode?.removeChild(link);
  },

  getAIFeedbackHistory: async (): Promise<AIFeedback[]> => {
    return apiClient('/api/v1/mlops/feedback/submit/');
  },
};
