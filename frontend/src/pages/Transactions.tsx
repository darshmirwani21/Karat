import { useQuery } from '@tanstack/react-query'
import { getTransactions } from '../services/api'
import './Transactions.css'

export default function Transactions() {
  const { data, isLoading } = useQuery({
    queryKey: ['transactions'],
    queryFn: getTransactions,
  })

  if (isLoading) {
    return <div className="transactions-loading">Loading transactions...</div>
  }

  return (
    <div className="transactions">
      <h1>Transactions</h1>
      
      <div className="transactions-filters">
        <input type="text" placeholder="Search transactions..." className="search-input" />
        <select className="filter-select">
          <option value="">All Categories</option>
          <option value="food">Food & Drink</option>
          <option value="transportation">Transportation</option>
          <option value="entertainment">Entertainment</option>
        </select>
      </div>

      <div className="transactions-table">
        <table>
          <thead>
            <tr>
              <th>Date</th>
              <th>Merchant</th>
              <th>Category</th>
              <th>Amount</th>
            </tr>
          </thead>
          <tbody>
            {data?.transactions?.length > 0 ? (
              data.transactions.map((transaction: any) => (
                <tr key={transaction.id}>
                  <td>{new Date(transaction.date).toLocaleDateString()}</td>
                  <td>{transaction.merchant_name || 'N/A'}</td>
                  <td>{transaction.category}</td>
                  <td className={transaction.amount < 0 ? 'expense' : 'income'}>
                    ${Math.abs(transaction.amount).toFixed(2)}
                  </td>
                </tr>
              ))
            ) : (
              <tr>
                <td colSpan={4} className="no-transactions">
                  No transactions found. Connect your bank account to get started.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  )
}

