import { useQuery } from '@tanstack/react-query'
import { getFinancialSummary, getSpendingByCategory, getMonthlyTrends, getAnomalies } from '../services/api'
import { PieChart, Pie, Cell, AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, Legend, RadialBarChart, RadialBar } from 'recharts'
import './Dashboard.css'

const COLORS = ["#4ade80", "#60a5fa", "#f472b6", "#fb923c", "#a78bfa", "#34d399", "#fbbf24", "#f87171"]

export default function Dashboard() {
  const { data: summary, isLoading: summaryLoading } = useQuery({
    queryKey: ['financialSummary'],
    queryFn: () => getFinancialSummary(),
  })

  const { data: categoryData, isLoading: categoryLoading } = useQuery({
    queryKey: ['spendingByCategory'],
    queryFn: () => getSpendingByCategory(),
  })

  const { data: trendsData, isLoading: trendsLoading } = useQuery({
    queryKey: ['monthlyTrends'],
    queryFn: () => getMonthlyTrends(),
  })

  const { data: anomaliesData, isLoading: anomaliesLoading } = useQuery({
    queryKey: ['anomalies'],
    queryFn: () => getAnomalies(),
  })

  if (summaryLoading || categoryLoading || trendsLoading || anomaliesLoading) {
    return <div className="dashboard-loading">Loading financial data...</div>
  }

  // Prepare data for savings rate radial chart
  const savingsRate = summary?.savings_ratio || 0
  const savingsData = [
    {
      name: 'Savings Rate',
      value: savingsRate * 100,
      fill: savingsRate > 0.15 ? '#4ade80' : savingsRate > 0.05 ? '#fbbf24' : '#f87171'
    }
  ]

  // Format category data for pie chart
  const pieData = categoryData?.categories?.map(cat => ({
    name: cat.category,
    value: cat.amount,
    percentage: cat.percentage
  })) || []

  // Custom tooltip for pie chart
  const CustomTooltip = ({ active, payload }: any) => {
    if (active && payload && payload.length) {
      return (
        <div className="custom-tooltip">
          <p className="tooltip-label">{payload[0].name}</p>
          <p className="tooltip-value">${payload[0].value.toFixed(2)}</p>
          <p className="tooltip-percentage">{payload[0].payload.percentage.toFixed(1)}%</p>
        </div>
      )
    }
    return null
  }

  return (
    <div className="dashboard">
      <div className="dashboard-header">
        <h1>Financial Dashboard</h1>
        <p className="last-updated">Last updated: {new Date().toLocaleString()}</p>
      </div>
      
      <div className="summary-cards">
        <div className="summary-card">
          <h3>Total Income</h3>
          <p className="amount">${summary?.total_income?.toFixed(2) || '0.00'}</p>
        </div>
        <div className="summary-card">
          <h3>Total Expenses</h3>
          <p className="amount expenses">${summary?.total_expenses?.toFixed(2) || '0.00'}</p>
        </div>
        <div className="summary-card">
          <h3>Total Savings</h3>
          <p className="amount savings">${summary?.total_savings?.toFixed(2) || '0.00'}</p>
        </div>
        <div className="summary-card">
          <h3>Savings Ratio</h3>
          <p className="amount">{(summary?.savings_ratio * 100 || 0).toFixed(1)}%</p>
        </div>
      </div>

      {/* Savings Rate Radial Chart */}
      <div className="dashboard-section">
        <h2>Savings Rate</h2>
        <div className="chart-container">
          <RadialBarChart cx="50%" cy="50%" innerRadius="60%" outerRadius="90%" data={savingsData}>
            <RadialBar dataKey="value" cornerRadius={10} fill={savingsData[0].fill} />
            <Tooltip />
          </RadialBarChart>
          <div className="savings-rate-label">
            <span className="savings-rate-value">{(savingsRate * 100).toFixed(1)}%</span>
            <span className="savings-rate-text">of income saved</span>
          </div>
        </div>
      </div>

      <div className="charts-row">
        <div className="dashboard-section chart-half">
          <h2>Spending by Category</h2>
          <div className="chart-container">
            {pieData.length > 0 ? (
              <PieChart width={400} height={300}>
                <Pie
                  data={pieData}
                  cx="50%"
                  cy="50%"
                  labelLine={false}
                  label={({ name, percentage }) => `${name}: ${percentage.toFixed(1)}%`}
                  outerRadius={80}
                  fill="#8884d8"
                  dataKey="value"
                >
                  {pieData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip content={<CustomTooltip />} />
              </PieChart>
            ) : (
              <p className="no-data">No spending data available</p>
            )}
          </div>
        </div>

        <div className="dashboard-section chart-half">
          <h2>Monthly Trends</h2>
          <div className="chart-container">
            {trendsData?.trends && trendsData.trends.length > 0 ? (
              <AreaChart width={400} height={300} data={trendsData.trends.reverse()}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="month" />
                <YAxis />
                <Tooltip formatter={(value: number) => `$${value.toFixed(2)}`} />
                <Legend />
                <Area type="monotone" dataKey="income" stackId="1" stroke="#60a5fa" fill="#60a5fa" name="Income" />
                <Area type="monotone" dataKey="expenses" stackId="2" stroke="#f87171" fill="#f87171" name="Expenses" />
              </AreaChart>
            ) : (
              <p className="no-data">No trend data available</p>
            )}
          </div>
        </div>
      </div>

      {/* Anomalies Section */}
      <div className="dashboard-section">
        <h2>Unusual Spending Detection</h2>
        <div className="anomalies-container">
          {anomaliesData?.anomalies && anomaliesData.anomalies.length > 0 ? (
            <div className="anomalies-list">
              {anomaliesData.anomalies.map((anomaly) => (
                <div key={anomaly.id} className="anomaly-card">
                  <div className="anomaly-header">
                    <span className="anomaly-merchant">{anomaly.merchant_name}</span>
                    <span className="anomaly-badge">⚠ Unusual</span>
                  </div>
                  <div className="anomaly-details">
                    <span className="anomaly-amount">${anomaly.amount.toFixed(2)}</span>
                    <span className="anomaly-category">{anomaly.category}</span>
                    <span className="anomaly-date">{new Date(anomaly.date).toLocaleDateString()}</span>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <p className="no-anomalies">No unusual spending detected ✓</p>
          )}
        </div>
      </div>
    </div>
  )
}

