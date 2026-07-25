export interface GraphNode {
  id: string;
  labels: string[];
  properties: Record<string, string | number | boolean | string[] | null | undefined>;
  x?: number;
  y?: number;
  vx?: number;
  vy?: number;
  fx?: number;
  fy?: number;
}

export interface GraphLink {
  source: string | GraphNode;
  target: string | GraphNode;
  type: string;
  properties: Record<string, string | number | boolean | string[] | null | undefined>;
}

export interface GraphData {
  nodes: GraphNode[];
  links: GraphLink[];
}
