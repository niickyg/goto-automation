import { Link, useLocation } from 'react-router-dom'
import { Home, Phone, CheckSquare, BarChart3, Settings, X, Menu } from 'lucide-react'
import { useAppStore } from '../store/appStore'
import { useActionItems } from '../hooks/useActionItems'
import { Badge } from './ui/badge'
import { Button } from './ui/button'
import { cn } from '@/lib/utils'

const navigation = [
  { name: 'Dashboard', href: '/', icon: Home },
  { name: 'Calls', href: '/calls', icon: Phone },
  { name: 'Action Items', href: '/actions', icon: CheckSquare, badge: true },
  { name: 'Analytics', href: '/analytics', icon: BarChart3 },
  { name: 'Settings', href: '/settings', icon: Settings },
]

export default function Sidebar() {
  const location = useLocation()
  const { sidebarOpen, toggleSidebar } = useAppStore()
  const { data: actionItemsData } = useActionItems({ status: 'pending' })
  
  const pendingCount = actionItemsData?.total || 0

  return (
    <>
      {/* Mobile overlay */}
      {sidebarOpen && (
        <div
          className="fixed inset-0 bg-black/50 lg:hidden z-40"
          onClick={toggleSidebar}
        />
      )}
      
      {/* Sidebar */}
      <div
        className={cn(
          "fixed inset-y-0 left-0 z-50 w-64 bg-gray-900 transform transition-transform duration-300 ease-in-out lg:translate-x-0 lg:static lg:inset-0",
          sidebarOpen ? "translate-x-0" : "-translate-x-full"
        )}
      >
        {/* Logo */}
        <div className="flex items-center justify-between h-16 px-6 bg-gray-800">
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <Phone className="h-8 w-8 text-blue-500" />
            </div>
            <div className="ml-3">
              <h1 className="text-white font-bold text-lg">GoTo Automation</h1>
              <p className="text-gray-400 text-xs">Call Dashboard</p>
            </div>
          </div>
          <Button
            variant="ghost"
            size="icon"
            className="lg:hidden text-gray-400 hover:text-white"
            onClick={toggleSidebar}
          >
            <X className="h-5 w-5" />
          </Button>
        </div>

        {/* Navigation */}
        <nav className="mt-6 px-3 space-y-1">
          {navigation.map((item) => {
            const isActive = location.pathname === item.href
            const Icon = item.icon
            
            return (
              <Link
                key={item.name}
                to={item.href}
                className={cn(
                  "flex items-center justify-between px-3 py-2 rounded-lg text-sm font-medium transition-colors",
                  isActive
                    ? "bg-gray-800 text-white"
                    : "text-gray-400 hover:bg-gray-800 hover:text-white"
                )}
              >
                <div className="flex items-center">
                  <Icon className="h-5 w-5 mr-3" />
                  <span>{item.name}</span>
                </div>
                {item.badge && pendingCount > 0 && (
                  <Badge variant="destructive" className="ml-auto">
                    {pendingCount}
                  </Badge>
                )}
              </Link>
            )
          })}
        </nav>

        {/* Bottom info */}
        <div className="absolute bottom-0 left-0 right-0 p-4 bg-gray-800">
          <div className="text-xs text-gray-400">
            <div className="flex items-center justify-between">
              <span>Version 1.0.0</span>
              <Badge variant="success">Live</Badge>
            </div>
          </div>
        </div>
      </div>
    </>
  )
}
