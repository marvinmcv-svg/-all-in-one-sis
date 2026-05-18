import useSWR from 'swr'

const fetcher = (url: string) => fetch(url).then((r) => r.json())

export function useSubscription() {
  const { data } = useSWR<{ success: boolean; data: { used: number; limit: number; unlimited: boolean } }>('/api/v1/ai/usage', fetcher)

  return {
    usage: data?.data,
    isPremium: data?.data?.unlimited ?? false,
  }
}
