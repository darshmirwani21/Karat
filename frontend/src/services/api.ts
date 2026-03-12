/**
 * Karat API client - calls backend endpoints
 */

const API_BASE = '/api';

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers: { 'Content-Type': 'application/json', ...options?.headers },
  });
  if (!res.ok) throw new Error(`API error: ${res.status}`);
  return res.json();
}

export interface FinancialSummary {
  total_income: number;
  total_expenses: number;
  total_savings: number;
  savings_ratio: number;
  account_balances: number[];
}

export async function getFinancialSummary(userId = 1): Promise<FinancialSummary> {
  return request<FinancialSummary>(`/dashboard/summary?user_id=${userId}`);
}

export interface SavingsGoal {
  id: number;
  name: string;
  target_amount: number;
  current_amount: number;
  target_date: string;
}

export async function getSavingsGoals(userId = 1): Promise<{ goals: SavingsGoal[] }> {
  return request<{ goals: SavingsGoal[] }>(`/planning/goals?user_id=${userId}`);
}

export interface Transaction {
  id: number;
  date: string;
  merchant_name: string | null;
  category: string;
  amount: number;
}

export async function getTransactions(userId = 1, accountId?: number): Promise<{ transactions: Transaction[] }> {
  const params = new URLSearchParams({ user_id: String(userId) });
  if (accountId != null) params.set('account_id', String(accountId));
  return request<{ transactions: Transaction[] }>(`/banking/transactions?${params}`);
}

/** Get a Plaid Link token to connect a bank account */
export async function getLinkToken(userId = 1): Promise<{ link_token: string }> {
  return request<{ link_token: string }>(`/banking/link_token?user_id=${userId}`);
}

/** Exchange public token after Plaid Link success */
export async function connectBank(publicToken: string, userId = 1): Promise<{ status: string; accounts: { id: number; name: string; type: string; balance: number }[] }> {
  return request<{ status: string; accounts: { id: number; name: string; type: string; balance: number }[] }>('/banking/connect', {
    method: 'POST',
    body: JSON.stringify({ public_token: publicToken, user_id: userId }),
  });
}

export async function getSpendingByCategory(userId = 1): Promise<{ categories: { category: string; amount: number; percentage: number; transaction_count: number }[] }> {
  return request<{ categories: { category: string; amount: number; percentage: number; transaction_count: number }[] }>(`/dashboard/spending/category?user_id=${userId}`);
}

export async function getMonthlyTrends(userId = 1, months = 6): Promise<{ trends: { month: string; income: number; expenses: number; savings: number; savings_ratio: number }[] }> {
  return request<{ trends: { month: string; income: number; expenses: number; savings: number; savings_ratio: number }[] }>(`/dashboard/trends/monthly?user_id=${userId}&months=${months}`);
}

export async function getSpendingForecast(userId = 1, weeks = 8): Promise<{ forecast: { week: number; predicted_spending: number }[]; message: string }> {
  return request<{ forecast: { week: number; predicted_spending: number }[]; message: string }>(`/dashboard/forecast?user_id=${userId}&weeks=${weeks}`);
}

export async function getAnomalies(userId = 1): Promise<{ anomalies: { id: number; amount: number; date: string; merchant_name: string; category: string; is_anomaly: boolean }[] }> {
  return request<{ anomalies: { id: number; amount: number; date: string; merchant_name: string; category: string; is_anomaly: boolean }[] }>(`/dashboard/anomalies?user_id=${userId}`);
}

export async function createGoal(name: string, targetAmount: number, targetDate: string, userId = 1): Promise<{ goal_id: number; status: string }> {
  return request<{ goal_id: number; status: string }>('/planning/goals', {
    method: 'POST',
    body: JSON.stringify({ 
      name, 
      target_amount: targetAmount, 
      target_date: targetDate,
      user_id: userId 
    }),
  });
}

export async function generateRecommendations(goalId: number): Promise<{ recommendations: { id: number; week_start: string; recommended_amount: number; reasoning: string; user_approved: boolean | null }[] }> {
  return request<{ recommendations: { id: number; week_start: string; recommended_amount: number; reasoning: string; user_approved: boolean | null }[] }>(`/planning/recommendations/generate?goal_id=${goalId}`, {
    method: 'POST',
  });
}

export async function approveRecommendation(recId: number, approved: boolean): Promise<{ status: string; learning: boolean }> {
  return request<{ status: string; learning: boolean }>(`/planning/recommendations/${recId}/approve?approved=${approved}`, {
    method: 'POST',
  });
}

export async function getRecommendations(goalId: number): Promise<{ recommendations: { id: number; week_start: string; recommended_amount: number; reasoning: string; user_approved: boolean | null }[] }> {
  return request<{ recommendations: { id: number; week_start: string; recommended_amount: number; reasoning: string; user_approved: boolean | null }[] }>(`/planning/recommendations?goal_id=${goalId}`);
}
