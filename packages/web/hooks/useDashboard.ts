import useSWR from 'swr'
import type { DashboardStats } from '@clearpath/shared-types'

const fetcher = (url: string) => fetch(url).then((r) => r.json())

export function useDashboard() {
  const { data, error, isLoading, mutate } = useSWR<{ success: boolean; data: DashboardStats }>('/api/v1/dashboard/stats', fetcher, {
    refreshInterval: 30000,
  })

  return {
    stats: data?.data,
    isLoading,
    error,
    mutate,
  }
}
