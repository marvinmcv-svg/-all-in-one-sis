'use client'

import useSWR from 'swr'

const fetcher = (url: string) => fetch(url).then((r) => r.json())

export function HealthTimeline() {
  const { data } = useSWR('/api/v1/dashboard/health-timeline', fetcher)
  const milestones = (data?.data ?? []).slice(0, 5) as Array<{
    id: string
    iconEmoji: string
    title: string
    description: string
    achieved: boolean
    targetDays: number
  }>

  return (
    <div className="bg-white rounded-2xl p-6 shadow-sm">
      <h2 className="text-lg font-semibold text-gray-900 mb-4">Health Recovery</h2>
      <div className="space-y-4">
        {milestones.map((m) => (
          <div key={m.id} className={`flex items-start gap-3 ${!m.achieved ? 'opacity-40' : ''}`}>
            <div className={`w-8 h-8 rounded-full flex items-center justify-center text-sm flex-shrink-0 ${m.achieved ? 'bg-green-100' : 'bg-gray-100'}`}>
              {m.iconEmoji}
            </div>
            <div>
              <div className="font-medium text-gray-900 text-sm">{m.title}</div>
              <div className="text-xs text-gray-500">{m.description}</div>
              {!m.achieved && <div className="text-xs text-gray-400 mt-0.5">{m.targetDays}+ days required</div>}
            </div>
            {m.achieved && <div className="ml-auto text-green-600 text-sm">✓</div>}
          </div>
        ))}
      </div>
    </div>
  )
}
