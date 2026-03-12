import { useState, useMemo } from 'react'
import { useQuery } from '@tanstack/react-query'
import { getTransactions } from '../services/api'
import './Transactions.css'

interface Transaction {
  id: number
  date: string
  merchant_name: string | null
  category: string
  amount: number
}

const CATEGORY_COLORS: { [key: string]: string } = {
  "food_and_drink": "#4ade80",
  "general_merchandise": "#60a5fa", 
  "transportation": "#f472b6",
  "gas_stations": "#fb923c",
  "groceries": "#a78bfa",
  "restaurants": "#34d399",
  "entertainment": "#fbbf24",
  "travel": "#f87171",
  "utilities": "#4ade80",
  "rent": "#60a5fa",
  "income": "#4ade80",
  "transfer": "#f472b6",
  "other": "#666"
}

export default function Transactions() {
  const [searchTerm, setSearchTerm] = useState('')
  const [selectedCategory, setSelectedCategory] = useState('')
  const [sortField, setSortField] = useState<'date' | 'amount'>('date')
  const [sortDirection, setSortDirection] = useState<'asc' | 'desc'>('desc')
  const [currentPage, setCurrentPage] = useState(1)
  const ITEMS_PER_PAGE = 25

  const { data, isLoading } = useQuery({
    queryKey: ['transactions'],
    queryFn: getTransactions,
  })

  // Get unique categories from transactions
  const categories = useMemo(() => {
    if (!data?.transactions) return []
    const uniqueCategories = Array.from(new Set(data.transactions.map(t => t.category)))
    return uniqueCategories.filter(Boolean).sort()
  }, [data])

  // Filter and sort transactions
  const filteredAndSortedTransactions = useMemo(() => {
    if (!data?.transactions) return []

    let filtered = data.transactions.filter((transaction: Transaction) => {
      const matchesSearch = !searchTerm || 
        transaction.merchant_name?.toLowerCase().includes(searchTerm.toLowerCase()) ||
        transaction.category.toLowerCase().includes(searchTerm.toLowerCase())
      
      const matchesCategory = !selectedCategory || transaction.category === selectedCategory
      
      return matchesSearch && matchesCategory
    })

    // Sort transactions
    filtered.sort((a: Transaction, b: Transaction) => {
      let aValue: any, bValue: any
      
      if (sortField === 'date') {
        aValue = new Date(a.date).getTime()
        bValue = new Date(b.date).getTime()
      } else {
        aValue = Math.abs(a.amount)
        bValue = Math.abs(b.amount)
      }

      if (sortDirection === 'asc') {
        return aValue - bValue
      } else {
        return bValue - aValue
      }
    })

    return filtered
  }, [data, searchTerm, selectedCategory, sortField, sortDirection])

  // Pagination
  const totalPages = Math.ceil(filteredAndSortedTransactions.length / ITEMS_PER_PAGE)
  const startIndex = (currentPage - 1) * ITEMS_PER_PAGE
  const paginatedTransactions = filteredAndSortedTransactions.slice(startIndex, startIndex + ITEMS_PER_PAGE)

  const handleSort = (field: 'date' | 'amount') => {
    if (sortField === field) {
      setSortDirection(sortDirection === 'asc' ? 'desc' : 'asc')
    } else {
      setSortField(field)
      setSortDirection('desc') // Default to desc for new field
    }
  }

  const formatAmount = (amount: number) => {
    const isIncome = amount < 0
    const formattedAmount = Math.abs(amount).toFixed(2)
    return {
      amount: formattedAmount,
      className: isIncome ? 'income' : 'expense',
      label: isIncome ? '(income)' : ''
    }
  }

  const getCategoryColor = (category: string) => {
    return CATEGORY_COLORS[category] || CATEGORY_COLORS.other
  }

  if (isLoading) {
    return <div className="transactions-loading">Loading transactions...</div>
  }

  return (
    <div className="transactions">
      <h1>Transactions</h1>
      
      <div className="transactions-filters">
        <input
          type="text"
          placeholder="Search transactions..."
          className="search-input"
          value={searchTerm}
          onChange={(e) => {
            setSearchTerm(e.target.value)
            setCurrentPage(1) // Reset to first page on search
          }}
        />
        <select
          className="filter-select"
          value={selectedCategory}
          onChange={(e) => {
            setSelectedCategory(e.target.value)
            setCurrentPage(1) // Reset to first page on filter
          }}
        >
          <option value="">All Categories</option>
          {categories.map(category => (
            <option key={category} value={category}>
              {category.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase())}
            </option>
          ))}
        </select>
      </div>

      <div className="transactions-summary">
        <span className="summary-text">
          Showing {startIndex + 1}-{Math.min(startIndex + ITEMS_PER_PAGE, filteredAndSortedTransactions.length)} of {filteredAndSortedTransactions.length} transactions
        </span>
      </div>

      <div className="transactions-table">
        <table>
          <thead>
            <tr>
              <th 
                className={`sortable ${sortField === 'date' ? 'active' : ''}`}
                onClick={() => handleSort('date')}
              >
                Date {sortField === 'date' && (sortDirection === 'asc' ? '↑' : '↓')}
              </th>
              <th>Merchant</th>
              <th>Category</th>
              <th 
                className={`sortable ${sortField === 'amount' ? 'active' : ''}`}
                onClick={() => handleSort('amount')}
              >
                Amount {sortField === 'amount' && (sortDirection === 'asc' ? '↑' : '↓')}
              </th>
            </tr>
          </thead>
          <tbody>
            {paginatedTransactions.length > 0 ? (
              paginatedTransactions.map((transaction: Transaction) => {
                const amountInfo = formatAmount(transaction.amount)
                return (
                  <tr key={transaction.id}>
                    <td>{new Date(transaction.date).toLocaleDateString()}</td>
                    <td>{transaction.merchant_name || 'N/A'}</td>
                    <td>
                      <span 
                        className="category-badge"
                        style={{ backgroundColor: getCategoryColor(transaction.category) }}
                      >
                        {transaction.category.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase())}
                      </span>
                    </td>
                    <td className={amountInfo.className}>
                      ${amountInfo.amount} {amountInfo.label}
                    </td>
                  </tr>
                )
              })
            ) : (
              <tr>
                <td colSpan={4} className="no-transactions">
                  {searchTerm || selectedCategory 
                    ? 'No transactions match your filters.'
                    : 'No transactions found. Connect your bank account to get started.'
                  }
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="pagination">
          <button
            className="pagination-button"
            onClick={() => setCurrentPage(currentPage - 1)}
            disabled={currentPage === 1}
          >
            Previous
          </button>
          
          <span className="pagination-info">
            Page {currentPage} of {totalPages}
          </span>
          
          <button
            className="pagination-button"
            onClick={() => setCurrentPage(currentPage + 1)}
            disabled={currentPage === totalPages}
          >
            Next
          </button>
        </div>
      )}
    </div>
  )
}

