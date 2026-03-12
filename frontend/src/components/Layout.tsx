import { ReactNode } from 'react'
import { Link, useLocation } from 'react-router-dom'
import './Layout.css'

interface LayoutProps {
  children: ReactNode
}

export default function Layout({ children }: LayoutProps) {
  const location = useLocation()

  return (
    <div className="layout">
      <nav className="navbar">
        <div className="nav-brand">
          <h1>Karat</h1>
        </div>
        <div className="nav-links">
          <Link 
            to="/" 
            className={location.pathname === '/' ? 'active' : ''}
          >
            Dashboard
          </Link>
          <Link 
            to="/goals" 
            className={location.pathname === '/goals' ? 'active' : ''}
          >
            Goals
          </Link>
          <Link 
            to="/transactions" 
            className={location.pathname === '/transactions' ? 'active' : ''}
          >
            Transactions
          </Link>
          <Link 
            to="/connect" 
            className={location.pathname === '/connect' ? 'active' : ''}
          >
            Connect Bank
          </Link>
        </div>
      </nav>
      <main className="main-content">
        {children}
      </main>
    </div>
  )
}

