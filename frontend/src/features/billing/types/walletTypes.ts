export interface WalletTransaction {
  amount: number;
  type: string;
  description: string;
  date: string;
}

export interface WalletLedgerResponse {
  history: WalletTransaction[];
  pagination?: {
    total_pages: number;
    page: number;
  };
}
