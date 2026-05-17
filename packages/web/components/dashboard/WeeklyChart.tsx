'use client'

import useSWR from 'swr'
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Legend } from 'recharts'

const fetcher = (url: string) => fetch(url).then((r) => r.json())

export function WeeklyChart() {
  const { data } = useSWR('/api/v1/dashboard/weekly-chart', fetcher)
  const chartData = data?.data ?? []

  return (
    <div className="bg-white rounded-2xl p-6 shadow-sm">
      <h2 className="text-lg font-semibold text-gray-900 mb-4">This Week</h2>
      <ResponsiveContainer width="100%" height={200}>
        <BarChart data={chartData}>
          <XAxis dataKey="date" tick={{ fontSize: 11 }} tickFormatter={(v: string) => v.slice(5)} />
          <YAxis tick={{ fontSize: 11 }} />
          <Tooltip />
          <Legend />
          <Bar dataKey="cravings" name="Cravings" fill="#ef4444" radius={4} />
          <Bar dataKey="beaten" name="Beaten" fill="#22c55e" radius={4} />
        </BarChart>
      </ResponsiveContainer>
    </div>
  )
}
