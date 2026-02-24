import { useQuery } from '@tanstack/react-query'
import { getFinancialSummary } from '../services/api'
import './Dashboard.css'

export default function Dashboard() {
  const { data, isLoading } = useQuery({
    queryKey: ['financialSummary'],
    queryFn: getFinancialSummary,
  })

  if (isLoading) {
    return <div className="dashboard-loading">Loading financial data...</div>
  }

  return (
    <div className="dashboard">
      <h1>Financial Dashboard</h1>
      
      <div className="summary-cards">
        <div className="summary-card">
          <h3>Total Income</h3>
          <p className="amount">${data?.total_income?.toFixed(2) || '0.00'}</p>
        </div>
        <div className="summary-card">
          <h3>Total Expenses</h3>
          <p className="amount">${data?.total_expenses?.toFixed(2) || '0.00'}</p>
        </div>
        <div className="summary-card">
          <h3>Total Savings</h3>
          <p className="amount savings">${data?.total_savings?.toFixed(2) || '0.00'}</p>
        </div>
        <div className="summary-card">
          <h3>Savings Ratio</h3>
          <p className="amount">{(data?.savings_ratio * 100 || 0).toFixed(1)}%</p>
        </div>
      </div>

      <div className="dashboard-section">
        <h2>Spending by Category</h2>
        <p className="placeholder">Chart will be displayed here</p>
      </div>

      <div className="dashboard-section">
        <h2>Monthly Trends</h2>
        <p className="placeholder">Trend chart will be displayed here</p>
      </div>
    </div>
  )
}

