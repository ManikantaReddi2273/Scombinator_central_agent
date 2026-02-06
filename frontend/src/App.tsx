import { Routes, Route, Navigate } from 'react-router-dom'
import { useAuthStore } from './store/authStore'
import LoginPage from './pages/LoginPage'
import DashboardLayout from './layouts/DashboardLayout'
import PriorityQueue from './pages/PriorityQueue'
import Drafts from './pages/Drafts'
import Companies from './pages/Companies'
import Emails from './pages/Emails'
import Dashboard from './pages/Dashboard'

function PrivateRoute({ children }: { children: React.ReactNode }) {
  const { isAuthenticated } = useAuthStore()
  return isAuthenticated ? <>{children}</> : <Navigate to="/login" replace />
}

function App() {
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route
        path="/"
        element={
          <PrivateRoute>
            <DashboardLayout />
          </PrivateRoute>
        }
      >
        <Route index element={<Dashboard />} />
        <Route path="priority-queue" element={<PriorityQueue />} />
        <Route path="drafts" element={<Drafts />} />
        <Route path="emails" element={<Emails />} />
        <Route path="companies" element={<Companies />} />
      </Route>
    </Routes>
  )
}

export default App

