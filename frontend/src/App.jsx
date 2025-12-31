import { Routes, Route, useLocation } from 'react-router-dom'
import { useEffect } from 'react'
import Sidebar from './components/Sidebar'
import TopBar from './components/TopBar'
import Dashboard from './components/Dashboard'
import CallList from './components/CallList'
import ActionItems from './components/ActionItems'
import { useAppStore } from './store/appStore'

// Placeholder components

function Analytics() {
  return (
    <div className="p-6">
      <h1 className="text-2xl font-bold mb-4">Analytics</h1>
      <p className="text-gray-600">Advanced analytics coming soon...</p>
    </div>
  )
}

function Settings() {
  return (
    <div className="p-6">
      <h1 className="text-2xl font-bold mb-4">Settings</h1>
      <p className="text-gray-600">Settings panel coming soon...</p>
    </div>
  )
}

const pageTitles = {
  '/': 'Dashboard',
  '/calls': 'Call History',
  '/actions': 'Action Items',
  '/analytics': 'Analytics',
  '/settings': 'Settings',
}

function App() {
  const location = useLocation()
  const { darkMode } = useAppStore()

  const pageTitle = pageTitles[location.pathname] || 'Dashboard'

  useEffect(() => {
    if (darkMode) {
      document.documentElement.classList.add('dark')
    } else {
      document.documentElement.classList.remove('dark')
    }
  }, [darkMode])

  return (
    <div className="flex h-screen bg-gray-50 overflow-hidden">
      {/* Sidebar */}
      <Sidebar />

      {/* Main content */}
      <div className="flex-1 flex flex-col overflow-hidden">
        {/* Top bar */}
        <TopBar title={pageTitle} />

        {/* Page content */}
        <main className="flex-1 overflow-y-auto bg-gray-50 p-6">
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/calls" element={<CallList />} />
            <Route path="/actions" element={<ActionItems />} />
            <Route path="/analytics" element={<Analytics />} />
            <Route path="/settings" element={<Settings />} />
          </Routes>
        </main>
      </div>
    </div>
  )
}

export default App
