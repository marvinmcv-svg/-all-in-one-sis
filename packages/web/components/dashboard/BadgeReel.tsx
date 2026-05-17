'use client'

import useSWR from 'swr'

const fetcher = (url: string) => fetch(url).then((r) => r.json())

export function BadgeReel() {
  const { data } = useSWR('/api/v1/dashboard/stats', fetcher)

  const placeholders = [
    { key: 'day_1', emoji: '🌱', title: '24 Hours' },
    { key: 'week_1', emoji: '🌳', title: 'One Week' },
    { key: 'month_1', emoji: '🏆', title: 'One Month' },
  ]

  return (
    <div className="bg-white rounded-2xl p-6 shadow-sm">
      <h2 className="text-lg font-semibold text-gray-900 mb-4">Recent Badges</h2>
      <div className="flex gap-4 overflow-x-auto pb-2">
        {placeholders.map((b) => (
          <div key={b.key} className="flex-shrink-0 flex flex-col items-center gap-2 opacity-40">
            <div className="w-16 h-16 bg-gray-100 rounded-full flex items-center justify-center text-2xl">{b.emoji}</div>
            <div className="text-xs text-gray-500 text-center">{b.title}</div>
          </div>
        ))}
        <div className="flex-shrink-0 flex items-center">
          <a href="/dashboard/badges" className="text-sm text-green-600 hover:text-green-700 font-medium whitespace-nowrap">View all →</a>
        </div>
      </div>
    </div>
  )
}
