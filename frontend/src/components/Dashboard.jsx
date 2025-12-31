import { useKPIDashboard, useDailyKPIs } from '../hooks/useKPIs'
import { useRecentCalls } from '../hooks/useCalls'
import { useActionItems } from '../hooks/useActionItems'
import { useAppStore } from '../store/appStore'
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from './ui/card'
import { Badge } from './ui/badge'
import { Button } from './ui/button'
import {
  Phone, Clock, TrendingUp, TrendingDown, CheckCircle,
  AlertCircle, Activity, Users, ArrowRight
} from 'lucide-react'
import {
  LineChart, Line, BarChart, Bar, PieChart, Pie, Cell,
  XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer
} from 'recharts'
import { formatDuration, formatPhoneNumber } from '@/lib/utils'
import { format } from 'date-fns'
import { Link } from 'react-router-dom'

function KPICard({ title, value, subtitle, icon: Icon, trend, loading }) {
  if (loading) {
    return (
      <Card>
        <CardContent className="p-6">
          <div className="animate-pulse">
            <div className="h-4 bg-gray-200 rounded w-1/2 mb-2"></div>
            <div className="h-8 bg-gray-200 rounded w-3/4"></div>
          </div>
        </CardContent>
      </Card>
    )
  }

  const trendColor = trend > 0 ? 'text-green-600' : trend < 0 ? 'text-red-600' : 'text-gray-600'
  const TrendIcon = trend > 0 ? TrendingUp : TrendingDown

  return (
    <Card className="hover:shadow-lg transition-shadow">
      <CardContent className="p-6">
        <div className="flex items-start justify-between">
          <div className="flex-1">
            <p className="text-sm font-medium text-muted-foreground">{title}</p>
            <h3 className="text-3xl font-bold mt-2">{value}</h3>
            {subtitle && (
              <p className="text-xs text-muted-foreground mt-1">{subtitle}</p>
            )}
            {trend !== undefined && trend !== 0 && (
              <div className={`flex items-center mt-2 text-sm ${trendColor}`}>
                <TrendIcon className="h-4 w-4 mr-1" />
                <span>{Math.abs(trend)}% vs last period</span>
              </div>
            )}
          </div>
          <div className="flex-shrink-0">
            <div className="p-3 bg-primary/10 rounded-lg">
              <Icon className="h-6 w-6 text-primary" />
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  )
}

function RecentCallItem({ call }) {
  const getSentimentColor = (sentiment) => {
    switch (sentiment) {
      case 'positive': return 'success'
      case 'negative': return 'destructive'
      default: return 'secondary'
    }
  }

  return (
    <div className="flex items-center justify-between py-3 border-b last:border-0">
      <div className="flex items-center flex-1 min-w-0">
        <div className="flex-shrink-0">
          <div className="h-10 w-10 rounded-full bg-blue-100 flex items-center justify-center">
            <Phone className="h-5 w-5 text-blue-600" />
          </div>
        </div>
        <div className="ml-3 flex-1 min-w-0">
          <p className="text-sm font-medium text-gray-900 truncate">
            {call.caller || 'Unknown'}
          </p>
          <p className="text-sm text-gray-500">
            {format(new Date(call.start_time), 'MMM d, h:mm a')} • {formatDuration(call.duration_seconds)}
          </p>
        </div>
      </div>
      <div className="ml-4 flex items-center space-x-2">
        {call.sentiment && (
          <Badge variant={getSentimentColor(call.sentiment)}>
            {call.sentiment}
          </Badge>
        )}
        {call.urgency && call.urgency >= 4 && (
          <Badge variant="warning">Urgent</Badge>
        )}
      </div>
    </div>
  )
}

export default function Dashboard() {
  const { selectedPeriod } = useAppStore()
  const { data: kpiData, isLoading: kpiLoading } = useKPIDashboard(selectedPeriod)
  const { data: dailyData } = useDailyKPIs(7)
  const { data: recentCallsData } = useRecentCalls(10)
  const { data: actionItemsData } = useActionItems({ page: 1, page_size: 5 })

  const SENTIMENT_COLORS = {
    positive: '#10b981',
    neutral: '#6b7280',
    negative: '#ef4444',
  }

  // Prepare sentiment data for pie chart
  const sentimentData = kpiData?.sentiment ? [
    { name: 'Positive', value: kpiData.sentiment.positive, color: SENTIMENT_COLORS.positive },
    { name: 'Neutral', value: kpiData.sentiment.neutral, color: SENTIMENT_COLORS.neutral },
    { name: 'Negative', value: kpiData.sentiment.negative, color: SENTIMENT_COLORS.negative },
  ].filter(item => item.value > 0) : []

  // Prepare daily volume data for chart
  const volumeData = dailyData?.slice().reverse().map(day => ({
    date: format(new Date(day.period_start), 'MMM d'),
    calls: day.total_calls,
    duration: Math.round(day.avg_duration_seconds / 60), // minutes
  })) || []

  if (kpiLoading) {
    return (
      <div className="space-y-6">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          {[1, 2, 3, 4].map(i => (
            <KPICard key={i} loading={true} />
          ))}
        </div>
      </div>
    )
  }

  const callVolume = kpiData?.call_volume || {}
  const sentiment = kpiData?.sentiment || {}
  const actionItems = kpiData?.action_items || {}

  return (
    <div className="space-y-6">
      {/* KPI Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <KPICard
          title="Total Calls"
          value={callVolume.total_calls || 0}
          subtitle={`${callVolume.inbound || 0} inbound • ${callVolume.outbound || 0} outbound`}
          icon={Phone}
          trend={12}
        />
        <KPICard
          title="Avg Duration"
          value={formatDuration(callVolume.avg_duration_seconds || 0)}
          subtitle="Per call this period"
          icon={Clock}
        />
        <KPICard
          title="Pending Actions"
          value={actionItems.pending || 0}
          subtitle={`${actionItems.completed || 0} completed`}
          icon={CheckCircle}
          trend={actionItems.total > 0 ? -5 : 0}
        />
        <KPICard
          title="Transcription Rate"
          value={`${Math.round(kpiData?.transcription_rate || 0)}%`}
          subtitle={`${kpiData?.calls_transcribed || 0} of ${callVolume.total_calls || 0} calls`}
          icon={Activity}
        />
      </div>

      {/* Charts Row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Call Volume Chart */}
        <Card>
          <CardHeader>
            <CardTitle>Call Volume Trend</CardTitle>
            <CardDescription>Daily call volume over the last 7 days</CardDescription>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={volumeData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="date" />
                <YAxis />
                <Tooltip />
                <Bar dataKey="calls" fill="#3b82f6" name="Calls" />
              </BarChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        {/* Sentiment Distribution */}
        <Card>
          <CardHeader>
            <CardTitle>Sentiment Distribution</CardTitle>
            <CardDescription>Overall call sentiment breakdown</CardDescription>
          </CardHeader>
          <CardContent>
            {sentimentData.length > 0 ? (
              <ResponsiveContainer width="100%" height={300}>
                <PieChart>
                  <Pie
                    data={sentimentData}
                    cx="50%"
                    cy="50%"
                    labelLine={false}
                    label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                    outerRadius={100}
                    fill="#8884d8"
                    dataKey="value"
                  >
                    {sentimentData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={entry.color} />
                    ))}
                  </Pie>
                  <Tooltip />
                </PieChart>
              </ResponsiveContainer>
            ) : (
              <div className="h-[300px] flex items-center justify-center text-muted-foreground">
                No sentiment data available
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Recent Activity & Quick Actions */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Recent Calls */}
        <Card>
          <CardHeader className="flex flex-row items-center justify-between">
            <div>
              <CardTitle>Recent Calls</CardTitle>
              <CardDescription>Latest call activity</CardDescription>
            </div>
            <Link to="/calls">
              <Button variant="ghost" size="sm">
                View All <ArrowRight className="ml-2 h-4 w-4" />
              </Button>
            </Link>
          </CardHeader>
          <CardContent>
            {recentCallsData && recentCallsData.length > 0 ? (
              <div className="space-y-1">
                {recentCallsData.slice(0, 5).map((call) => (
                  <RecentCallItem key={call.id} call={call} />
                ))}
              </div>
            ) : (
              <div className="text-center py-8 text-muted-foreground">
                No recent calls
              </div>
            )}
          </CardContent>
        </Card>

        {/* Recent Action Items */}
        <Card>
          <CardHeader className="flex flex-row items-center justify-between">
            <div>
              <CardTitle>Pending Actions</CardTitle>
              <CardDescription>Items requiring attention</CardDescription>
            </div>
            <Link to="/actions">
              <Button variant="ghost" size="sm">
                View All <ArrowRight className="ml-2 h-4 w-4" />
              </Button>
            </Link>
          </CardHeader>
          <CardContent>
            {actionItemsData && actionItemsData.action_items?.length > 0 ? (
              <div className="space-y-3">
                {actionItemsData.action_items.slice(0, 5).map((item) => (
                  <div key={item.id} className="flex items-start space-x-3 py-2 border-b last:border-0">
                    <CheckCircle className="h-5 w-5 text-gray-400 mt-0.5" />
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium text-gray-900">{item.description}</p>
                      <div className="flex items-center mt-1 space-x-2">
                        {item.priority && (
                          <Badge variant={item.priority >= 4 ? 'destructive' : 'secondary'} className="text-xs">
                            Priority {item.priority}
                          </Badge>
                        )}
                        {item.assigned_to && (
                          <span className="text-xs text-muted-foreground">
                            Assigned to {item.assigned_to}
                          </span>
                        )}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-center py-8 text-muted-foreground">
                No pending action items 🎉
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Stats Grid */}
      <Card>
        <CardHeader>
          <CardTitle>Quick Stats</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="text-center p-4 bg-gray-50 rounded-lg">
              <p className="text-2xl font-bold text-primary">{sentiment.positive || 0}</p>
              <p className="text-sm text-muted-foreground mt-1">Positive Calls</p>
            </div>
            <div className="text-center p-4 bg-gray-50 rounded-lg">
              <p className="text-2xl font-bold text-gray-600">{sentiment.neutral || 0}</p>
              <p className="text-sm text-muted-foreground mt-1">Neutral Calls</p>
            </div>
            <div className="text-center p-4 bg-gray-50 rounded-lg">
              <p className="text-2xl font-bold text-red-600">{sentiment.negative || 0}</p>
              <p className="text-sm text-muted-foreground mt-1">Negative Calls</p>
            </div>
            <div className="text-center p-4 bg-gray-50 rounded-lg">
              <p className="text-2xl font-bold text-green-600">
                {actionItems.total > 0 ? Math.round(actionItems.completion_rate) : 0}%
              </p>
              <p className="text-sm text-muted-foreground mt-1">Completion Rate</p>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
