'use client'

import useSWR from 'swr'

const fetcher = (url: string) => fetch(url).then((r) => r.json())

interface Props {
  type: 'days' | 'streak' | 'money' | 'cravings'
}

export function StatsCard({ type }: Props) {
  const { data } = useSWR('/api/v1/dashboard/stats', fetcher)
  const stats = data?.data

  const config = {
    days: {
      label: 'Days Clean',
      value: stats?.daysClean ?? '—',
      icon: '🌱',
      color: 'text-green-600',
    },
    streak: {
      label: 'Current Streak',
      value: stats ? `${stats.currentStreakDays}d` : '—',
      icon: '🔥',
      color: 'text-orange-500',
    },
    money: {
      label: 'Money Saved',
      value: stats ? `$${(stats.moneySavedCents / 100).toFixed(0)}` : '—',
      icon: '💰',
      color: 'text-blue-600',
    },
    cravings: {
      label: 'Beaten This Week',
      value: stats?.cravingsBeatThisWeek ?? '—',
      icon: '⚡',
      color: 'text-purple-600',
    },
  }

  const c = config[type]

  return (
    <div className="bg-white rounded-2xl p-6 shadow-sm">
      <div className="text-2xl mb-2">{c.icon}</div>
      <div className={`text-3xl font-bold ${c.color}`}>{c.value}</div>
      <div className="text-sm text-gray-500 mt-1">{c.label}</div>
    </div>
  )
}
