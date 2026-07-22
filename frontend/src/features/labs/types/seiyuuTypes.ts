export interface SeiyuuResult {
  id: number;
  name: string;
  language: 'japanese' | 'french' | 'other';
  origin: 'dataset' | 'youtube' | 'upload';
  definition?: string;
  roles?: string;
  impact?: string;
  origin_detail?: string;
  sample_url: string;
}

export interface SeiyuuApiResponse {
  query: string;
  results: SeiyuuResult[];
}
