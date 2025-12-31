import { useQuery } from '@tanstack/react-query'
import api from '../api'

export function useKPIDashboard(period = 'today') {
  return useQuery({
    queryKey: ['kpi', 'dashboard', period],
    queryFn: async () => {
      const response = await api.get(`/kpi/dashboard?period=${period}`)
      return response.data
    },
    refetchInterval: 10000, // Auto-refresh every 10 seconds
  })
}

export function useDailyKPIs(days = 7) {
  return useQuery({
    queryKey: ['kpi', 'daily', days],
    queryFn: async () => {
      const response = await api.get(`/kpi/daily?days=${days}`)
      return response.data
    },
  })
}
