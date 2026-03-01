import { Outlet, NavLink, useNavigate } from 'react-router-dom'
import { useAuthStore } from '../store/authStore'
import {
  LayoutDashboard,
  Mail,
  FileText,
  Building2,
  TrendingUp,
  LogOut,
  Menu,
  X,
  Send,
  Users,
} from 'lucide-react'
import { useState } from 'react'
import { Button } from '../components/ui/button'

export default function DashboardLayout() {
  const { adminEmail, logout } = useAuthStore()
  const navigate = useNavigate()
  const [sidebarOpen, setSidebarOpen] = useState(true)

  const handleLogout = () => {
    logout()
    navigate('/login')
  }

  const navItems = [
    { to: '/', icon: LayoutDashboard, label: 'Dashboard' },
    { to: '/priority-queue', icon: TrendingUp, label: 'Priority Queue' },
    { to: '/drafts', icon: FileText, label: 'Drafts' },
    { to: '/emails', icon: Mail, label: 'Emails' },
    { to: '/outbound/b2b', icon: Send, label: 'B2B Outbound' },
    { to: '/outbound/b2c', icon: Users, label: 'B2C Outreach' },
    { to: '/companies', icon: Building2, label: 'Companies' },
  ]

  return (
    <div className="min-h-screen bg-[#EAEFEF] text-gray-900">
      {/* Sidebar */}
      <aside
        className={`fixed left-0 top-0 z-40 h-screen w-64 bg-white border-r border-gray-200 shadow-lg transition-transform ${
          sidebarOpen ? 'translate-x-0' : '-translate-x-full'
        } lg:translate-x-0`}
      >
        <div className="flex h-full flex-col">
          {/* Logo */}
          <div className="flex h-16 items-center justify-between border-b border-gray-200 px-6 bg-gradient-to-r from-gray-300 to-gray-400">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 bg-white rounded-lg flex items-center justify-center shadow-md">
                <span className="text-xl font-bold text-gray-700">S</span>
              </div>
              <div>
                <h1 className="font-bold text-lg text-gray-900">S Combinator</h1>
                <p className="text-xs text-gray-700">Agent Platform</p>
              </div>
            </div>
            <Button
              variant="ghost"
              size="icon"
              className="lg:hidden text-gray-700 hover:bg-white/20"
              onClick={() => setSidebarOpen(false)}
            >
              <X className="w-5 h-5" />
            </Button>
          </div>

          {/* Navigation */}
          <nav className="flex-1 space-y-1 p-4 bg-[#EAEFEF]">
            {navItems.map((item) => {
              const Icon = item.icon
              return (
                <NavLink
                  key={item.to}
                  to={item.to}
                  className={({ isActive }) =>
                    `flex items-center gap-3 rounded-lg px-4 py-3 text-sm font-medium transition-colors ${
                      isActive
                        ? 'bg-gradient-to-r from-gray-300 to-gray-400 text-gray-900 shadow-md'
                        : 'text-gray-700 hover:bg-white hover:text-gray-900'
                    }`
                  }
                >
                  <Icon className="w-5 h-5" />
                  {item.label}
                </NavLink>
              )
            })}
          </nav>

          {/* User Section */}
          <div className="border-t border-gray-200 p-4 bg-white">
            <div className="mb-3 px-4 py-2 rounded-lg bg-[#EAEFEF]">
              <p className="text-xs text-gray-500 mb-1">Logged in as</p>
              <p className="text-sm font-medium text-gray-900 truncate">{adminEmail}</p>
            </div>
            <Button
              variant="ghost"
              className="w-full justify-start text-gray-700 hover:text-gray-900 hover:bg-[#EAEFEF]"
              onClick={handleLogout}
            >
              <LogOut className="w-4 h-4 mr-2" />
              Logout
            </Button>
          </div>
        </div>
      </aside>

      {/* Mobile sidebar overlay */}
      {sidebarOpen && (
        <div
          className="fixed inset-0 z-30 bg-black/50 lg:hidden"
          onClick={() => setSidebarOpen(false)}
        />
      )}

      {/* Main Content */}
      <div className="lg:pl-64">
        {/* Top Bar */}
        <header className="sticky top-0 z-30 flex h-16 items-center gap-4 border-b border-gray-200 bg-white/95 backdrop-blur px-6 shadow-sm">
          <Button
            variant="ghost"
            size="icon"
            className="lg:hidden text-gray-600 hover:text-gray-900"
            onClick={() => setSidebarOpen(true)}
          >
            <Menu className="w-5 h-5" />
          </Button>
          <div className="flex-1" />
        </header>

        {/* Page Content */}
        <main className="p-6">
          <Outlet />
        </main>
      </div>
    </div>
  )
}

