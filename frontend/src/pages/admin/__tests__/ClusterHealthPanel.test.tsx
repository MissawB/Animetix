import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { vi, describe, it, expect, beforeEach } from 'vitest';
import ClusterHealthPanel from '../ClusterHealthPanel';

const mockUseClusterHealth = vi.fn();
vi.mock('../../../features/admin/hooks/useHealth', () => ({
  useClusterHealth: () => mockUseClusterHealth(),
}));

const renderPanel = () => {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={qc}>
      <MemoryRouter>
        <ClusterHealthPanel />
      </MemoryRouter>
    </QueryClientProvider>,
  );
};

const mockClusterData = {
  timestamp: '2026-07-21T22:00:00Z',
  global_status: 'healthy',
  online_count: 4,
  total_count: 4,
  health_percentage: 100,
  nodes: [
    {
      id: 'gpu-node-1',
      name: 'GPU Worker 01',
      type: 'gpu',
      status: 'online',
      latency_ms: 12,
      details: {
        gpu_count: 2,
        total_vram_gb: 48,
        avg_temperature_c: 62,
        avg_utilization_pct: 75,
        cuda_version: '12.2',
        driver_version: '535.104.05',
      },
      gpus: [
        {
          id: 0,
          name: 'RTX 4090 #0',
          temperature_c: 60,
          utilization_pct: 80,
          memory_used_gb: 18,
          memory_total_gb: 24,
          status: 'active',
        },
        {
          id: 1,
          name: 'RTX 4090 #1',
          temperature_c: 64,
          utilization_pct: 70,
          memory_used_gb: 12,
          memory_total_gb: 24,
          status: 'active',
        },
      ],
    },
    {
      id: 'inference-node-1',
      name: 'vLLM Service',
      type: 'inference',
      status: 'online',
      latency_ms: 45,
      details: {
        engine: 'vLLM v0.4.0',
        model_count: 2,
        loaded_models: ['Mistral-7B-Instruct', 'Llama-3-8B'],
      },
    },
    {
      id: 'graph-db-1',
      name: 'Neo4j Main',
      type: 'graph_db',
      status: 'online',
      latency_ms: 8,
      details: {
        node_count: 15420,
        relationship_count: 89300,
        database: 'neo4j',
        bolt_uri: 'bolt://localhost:7687',
      },
    },
    {
      id: 'worker-node-1',
      name: 'Celery Queue',
      type: 'worker',
      status: 'online',
      latency_ms: 15,
      details: {
        queue_length: 3,
        worker_status: 'active',
        active_task: 'generate_embedding_batch',
        fallback_mode: 'nominal',
      },
    },
  ],
};

describe('ClusterHealthPanel', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders loading state when query is pending and no data', () => {
    mockUseClusterHealth.mockReturnValue({
      isPending: true,
      data: undefined,
      error: null,
      isFetching: true,
      refetch: vi.fn(),
    });

    const { container } = renderPanel();
    expect(container.querySelector('.animate-pulse')).toBeInTheDocument();
    expect(screen.queryByText('Cluster Status')).not.toBeInTheDocument();
  });

  it('renders error state when cluster is unreachable', () => {
    mockUseClusterHealth.mockReturnValue({
      isPending: false,
      data: undefined,
      error: new Error('Connection refused'),
      isFetching: false,
      refetch: vi.fn(),
    });

    renderPanel();
    expect(screen.getByText('Cluster Unreachable')).toBeInTheDocument();
    expect(screen.getByText('Connection refused')).toBeInTheDocument();
  });

  it('renders cluster nodes and global metrics when data is loaded', () => {
    const mockRefetch = vi.fn();
    mockUseClusterHealth.mockReturnValue({
      isPending: false,
      data: mockClusterData,
      error: null,
      isFetching: false,
      dataUpdatedAt: Date.now(),
      refetch: mockRefetch,
    });

    renderPanel();

    expect(screen.getByText('GPU Worker 01')).toBeInTheDocument();
    expect(screen.getByText('vLLM Service')).toBeInTheDocument();
    expect(screen.getByText('Neo4j Main')).toBeInTheDocument();
    expect(screen.getByText('Celery Queue')).toBeInTheDocument();

    // Check GPU node details
    expect(screen.getByText('CUDA 12.2')).toBeInTheDocument();
    expect(screen.getByText('Driver 535.104.05')).toBeInTheDocument();
    expect(screen.getByText('RTX 4090 #0')).toBeInTheDocument();
    expect(screen.getByText('RTX 4090 #1')).toBeInTheDocument();

    // Check inference node details
    expect(screen.getByText('vLLM v0.4.0')).toBeInTheDocument();
    expect(screen.getByText('Mistral-7B-Instruct')).toBeInTheDocument();
    expect(screen.getByText('Llama-3-8B')).toBeInTheDocument();

    // Check Graph DB node details
    expect(screen.getByText('15 420')).toBeInTheDocument();
    expect(screen.getByText('89 300')).toBeInTheDocument();

    // Test Refresh button
    const refreshButton = screen.getByRole('button', { name: /Refresh/i });
    fireEvent.click(refreshButton);
    expect(mockRefetch).toHaveBeenCalledTimes(1);
  });
});
