import { useState, useEffect } from 'react';
import { getGraphNeighborhood } from '../../api';

export interface GraphNode {
  id: string;
  labels: string[];
  properties: Record<string, any>;
  [key: string]: any;
}

export interface GraphLink {
  source: string;
  target: string;
  type: string;
  properties: Record<string, any>;
  [key: string]: any;
}

export interface GraphData {
  nodes: GraphNode[];
  links: GraphLink[];
}

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
        const result = await getGraphNeighborhood(id, type, depth);
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
