export interface ToTNode {
  id: string;
  type: 'root' | 'selected' | 'pruned' | 'final';
  score: number;
  full_text: string;
  label?: string;
  x?: number;
  y?: number;
}

export interface ToTLink {
  source: string | ToTNode;
  target: string | ToTNode;
}

export interface ToTGraphData {
  nodes: ToTNode[];
  links: ToTLink[];
}

export interface ToTResponse {
  full_tree: ToTGraphData;
  final_answer: string;
}
