import useSWR from 'swr'
import type { CravingLog } from '@clearpath/shared-types'

const fetcher = (url: string) => fetch(url).then((r) => r.json())

export function useCravingLogs() {
  const { data, error, isLoading, mutate } = useSWR<{ success: boolean; data: CravingLog[] }>('/api/v1/cravings', fetcher)

  return {
    logs: data?.data,
    isLoading,
    error,
    mutate,
  }
}
