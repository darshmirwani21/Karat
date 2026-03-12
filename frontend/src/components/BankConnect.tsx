import { useState, useEffect } from 'react'
import { getLinkToken, connectBank, getTransactions } from '../services/api'
import './BankConnect.css'

interface Account {
  id: number
  name: string
  type: string
  balance: number
}

export default function BankConnect() {
  const [isPlaidLoaded, setIsPlaidLoaded] = useState(false)
  const [linkToken, setLinkToken] = useState<string | null>(null)
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [connectedAccounts, setConnectedAccounts] = useState<Account[]>([])
  const [isConnecting, setIsConnecting] = useState(false)

  // Load Plaid script dynamically
  useEffect(() => {
    const script = document.createElement('script')
    script.src = 'https://cdn.plaid.com/link/v2/stable/link-initialize.js'
    script.async = true
    script.onload = () => setIsPlaidLoaded(true)
    document.body.appendChild(script)

    // Fetch existing accounts on component mount
    fetchAccounts()

    return () => {
      document.body.removeChild(script)
    }
  }, [])

  const fetchAccounts = async () => {
    try {
      const response = await getTransactions()
      if (response.transactions && response.transactions.length > 0) {
        // Extract unique accounts from transactions
        const uniqueAccounts = Array.from(
          new Map(response.transactions.map(t => [t.account_id, {
            id: t.account_id,
            name: `Account ${t.account_id}`,
            type: 'checking',
            balance: 0
          }]))
        ).map(([_, account]) => account)
        setConnectedAccounts(uniqueAccounts)
      }
    } catch (err) {
      console.error('Failed to fetch accounts:', err)
    }
  }

  const handleConnectBank = async () => {
    setIsLoading(true)
    setError(null)

    try {
      const response = await getLinkToken()
      setLinkToken(response.link_token)
    } catch (err: any) {
      if (err.status === 503) {
        // Plaid not configured - show demo mode notice
        setError('Demo mode — using synthetic data. Connect Plaid credentials to sync a real bank account.')
      } else {
        setError('Failed to get link token. Please try again.')
      }
      setIsLoading(false)
    }
  }

  const initializePlaidLink = () => {
    if (!window.Plaid || !linkToken) return

    setIsConnecting(true)

    const handler = window.Plaid.create({
      token: linkToken,
      onSuccess: async (public_token: string) => {
        try {
          const response = await connectBank(public_token)
          setConnectedAccounts(response.accounts)
          setLinkToken(null)
          setIsConnecting(false)
        } catch (err) {
          setError('Failed to connect bank. Please try again.')
          setIsConnecting(false)
        }
      },
      onLoad: () => {
        setIsLoading(false)
      },
      onExit: (err: any, metadata: any) => {
        console.log('Plaid Link exited:', err, metadata)
        setIsConnecting(false)
        setIsLoading(false)
      }
    })

    handler.open()
  }

  // Initialize Plaid Link when we have a link token
  useEffect(() => {
    if (linkToken && isPlaidLoaded) {
      initializePlaidLink()
    }
  }, [linkToken, isPlaidLoaded])

  return (
    <div className="bank-connect">
      <div className="bank-connect-header">
        <h1>Connect Bank Account</h1>
        <p>Securely connect your bank account to track your finances automatically.</p>
      </div>

      {error && (
        <div className="notice demo-notice">
          <span className="notice-icon">ℹ️</span>
          <span className="notice-text">{error}</span>
        </div>
      )}

      <div className="connect-section">
        <button
          className="btn-connect"
          onClick={handleConnectBank}
          disabled={isLoading || isConnecting}
        >
          {isLoading ? 'Loading...' : 'Connect Bank Account'}
        </button>
      </div>

      {connectedAccounts.length > 0 && (
        <div className="connected-accounts">
          <h2>Connected Accounts</h2>
          <div className="accounts-list">
            {connectedAccounts.map((account) => (
              <div key={account.id} className="account-card">
                <div className="account-info">
                  <h3>{account.name}</h3>
                  <p className="account-type">{account.type}</p>
                </div>
                <div className="account-balance">
                  <span className="balance-amount">${account.balance.toFixed(2)}</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {isConnecting && (
        <div className="connecting-overlay">
          <div className="connecting-modal">
            <div className="spinner"></div>
            <p>Connecting to your bank...</p>
          </div>
        </div>
      )}
    </div>
  )
}

// Add Plaid types to window object
declare global {
  interface Window {
    Plaid: {
      create: (config: any) => {
        open: () => void
        exit: () => void
      }
    }
  }
}
