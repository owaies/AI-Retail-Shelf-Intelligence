import type { ReactNode } from 'react'
import { NavLink } from 'react-router-dom'

const navigation = [
  ['/', 'Dashboard'],
  ['/analyze', 'Analyze'],
  ['/history', 'History'],
  ['/analytics', 'Analytics'],
  ['/settings', 'Settings'],
] as const

export function AppShell({ children }: { children: ReactNode }) {
  return (
    <div className="app-shell">
      <header className="topbar">
        <NavLink className="brand" to="/" aria-label="Retail Vision Intelligence home">
          <span className="brand-mark" aria-hidden="true">RV</span>
          <span>
            <strong>RETAIL VISION</strong>
            <small>INTELLIGENCE / 01</small>
          </span>
        </NavLink>
        <nav className="nav" aria-label="Primary navigation">
          {navigation.map(([to, label]) => (
            <NavLink key={to} to={to} className={({ isActive }) => isActive ? 'nav-link active' : 'nav-link'}>
              {label}
            </NavLink>
          ))}
        </nav>
        <div className="system-status" aria-label="System status">
          <span className="status-dot" aria-hidden="true" />
          <span>FOUNDATION ONLINE</span>
        </div>
      </header>
      <main className="page-content">{children}</main>
    </div>
  )
}
