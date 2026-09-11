import type { ReactNode } from 'react'
import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom'
import { AppShell } from './components/AppShell'
import { AnalyticsPage, AnalyzePage, DashboardPage, HistoryPage, LoginPage, SettingsPage, Day4AnalyticsPage, Day4HistoryPage } from './pages'
import { getAccessToken } from './services/auth'
import './styles.css'

function Protected({ children }: { children: ReactNode }) {
  return getAccessToken() ? <>{children}</> : <Navigate to="/login" replace />
}

function NotFound() {
  return <section className="empty-panel"><strong>ROUTE NOT FOUND</strong><p>The requested workspace does not exist.</p></section>
}

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<LoginPage />} />
        <Route path="/" element={<Protected><AppShell><DashboardPage /></AppShell></Protected>} />
        <Route path="/analyze" element={<Protected><AppShell><AnalyzePage /></AppShell></Protected>} />
        <Route path="/history" element={<Protected><AppShell><Day4HistoryPage /></AppShell></Protected>} />
        <Route path="/analytics" element={<Protected><AppShell><Day4AnalyticsPage /></AppShell></Protected>} />
        <Route path="/settings" element={<Protected><AppShell><SettingsPage /></AppShell></Protected>} />
        <Route path="*" element={<NotFound />} />
      </Routes>
    </BrowserRouter>
  )
}
