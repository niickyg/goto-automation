import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import api from '../api'
import toast from 'react-hot-toast'

export function useActionItems(params = {}) {
  return useQuery({
    queryKey: ['actionItems', params],
    queryFn: async () => {
      const response = await api.get('/actions', { params })
      return response.data
    },
  })
}

export function useUpdateActionItem() {
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: async ({ actionId, data }) => {
      const response = await api.patch(`/actions/${actionId}`, data)
      return response.data
    },
    onSuccess: () => {
      queryClient.invalidateQueries(['actionItems'])
      toast.success('Action item updated')
    },
    onError: (error) => {
      toast.error('Failed to update action item')
      console.error('Update error:', error)
    },
  })
}

export function useCompleteActionItem() {
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: async (actionId) => {
      const response = await api.post(`/actions/${actionId}/complete`)
      return response.data
    },
    onSuccess: () => {
      queryClient.invalidateQueries(['actionItems'])
      toast.success('Action item completed! ✓')
    },
    onError: () => {
      toast.error('Failed to complete action item')
    },
  })
}
