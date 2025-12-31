import { Menu, Search, Bell, Moon, Sun } from 'lucide-react'
import { useAppStore } from '../store/appStore'
import { Button } from './ui/button'
import { Badge } from './ui/badge'

const periods = [
  { value: 'today', label: 'Today' },
  { value: 'week', label: 'This Week' },
  { value: 'month', label: 'This Month' },
]

export default function TopBar({ title }) {
  const { toggleSidebar, darkMode, toggleDarkMode, selectedPeriod, setPeriod } = useAppStore()

  return (
    <div className="bg-white border-b border-gray-200 h-16 flex items-center justify-between px-6">
      {/* Left side */}
      <div className="flex items-center space-x-4">
        <Button
          variant="ghost"
          size="icon"
          className="lg:hidden"
          onClick={toggleSidebar}
        >
          <Menu className="h-5 w-5" />
        </Button>
        
        <div>
          <h2 className="text-xl font-semibold text-gray-900">{title}</h2>
        </div>
      </div>

      {/* Right side */}
      <div className="flex items-center space-x-4">
        {/* Period selector */}
        <div className="hidden md:flex items-center space-x-2">
          {periods.map((period) => (
            <Button
              key={period.value}
              variant={selectedPeriod === period.value ? "default" : "outline"}
              size="sm"
              onClick={() => setPeriod(period.value)}
            >
              {period.label}
            </Button>
          ))}
        </div>

        {/* Search */}
        <Button variant="outline" size="icon" className="hidden md:inline-flex">
          <Search className="h-4 w-4" />
        </Button>

        {/* Notifications */}
        <Button variant="outline" size="icon" className="relative">
          <Bell className="h-4 w-4" />
          <Badge 
            variant="destructive" 
            className="absolute -top-1 -right-1 h-5 w-5 flex items-center justify-center p-0 text-xs"
          >
            3
          </Badge>
        </Button>

        {/* Dark mode toggle */}
        <Button variant="outline" size="icon" onClick={toggleDarkMode}>
          {darkMode ? <Sun className="h-4 w-4" /> : <Moon className="h-4 w-4" />}
        </Button>
      </div>
    </div>
  )
}
