import { useState, useEffect } from 'react';
import { graphService } from './services/graphService';
import { GraphData } from '../../types';

export function useGraphData(id: string, type: string, depth: number) {
  const [data, setData] = useState<GraphData>({ nodes: [], links: [] });
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<Error | null>(null);

  useEffect(() => {
    let isMounted = true;

    async function fetchData() {
      if (!id || !type) return;

      setIsLoading(true);
      setError(null);

      try {
        const result = await graphService.getGraphNeighborhood(id, type, depth);
        if (isMounted) {
          setData(result);
        }
      } catch (err) {
        if (isMounted) {
          setError(err instanceof Error ? err : new Error(String(err)));
        }
      } finally {
        if (isMounted) {
          setIsLoading(false);
        }
      }
    }

    fetchData();

    return () => {
      isMounted = false;
    };
  }, [id, type, depth]);

  return { data, isLoading, error };
}
