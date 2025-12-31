import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import api from '../api'

export function useCalls(params = {}) {
  return useQuery({
    queryKey: ['calls', params],
    queryFn: async () => {
      const response = await api.get('/calls', { params })
      return response.data
    },
    staleTime: 10000, // 10 seconds
  })
}

export function useCall(callId) {
  return useQuery({
    queryKey: ['call', callId],
    queryFn: async () => {
      const response = await api.get(`/calls/${callId}`)
      return response.data
    },
    enabled: !!callId,
  })
}

export function useRecentCalls(limit = 10) {
  return useQuery({
    queryKey: ['calls', 'recent', limit],
    queryFn: async () => {
      const response = await api.get(`/calls/recent/summary?limit=${limit}`)
      return response.data.recent_calls || []
    },
    refetchInterval: 10000, // Auto-refresh every 10 seconds
  })
}
