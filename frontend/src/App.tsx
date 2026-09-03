import { BrowserRouter, Routes, Route } from 'react-router-dom'
import { AppShell } from './components/AppShell'
import { AnalyticsPage, AnalyzePage, DashboardPage, HistoryPage, SettingsPage } from './pages'
import './styles.css'

function NotFound() {
  return <section className="empty-panel"><strong>ROUTE NOT FOUND</strong><p>The requested workspace does not exist.</p></section>
}

export default function App() {
  return (
    <BrowserRouter>
      <AppShell>
        <Routes>
          <Route path="/" element={<DashboardPage />} />
          <Route path="/analyze" element={<AnalyzePage />} />
          <Route path="/history" element={<HistoryPage />} />
          <Route path="/analytics" element={<AnalyticsPage />} />
          <Route path="/settings" element={<SettingsPage />} />
          <Route path="*" element={<NotFound />} />
        </Routes>
      </AppShell>
    </BrowserRouter>
  )
}
