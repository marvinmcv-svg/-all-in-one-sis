'use client'

import { useState } from 'react'
import { CravingLogForm } from '@/components/track/CravingLogForm'
import { UsageLogForm } from '@/components/track/UsageLogForm'
import { useCravingLogs } from '@/hooks/useCravingLogs'
import { formatDistanceToNow } from 'date-fns'

export default function TrackPage() {
  const [activeTab, setActiveTab] = useState<'log' | 'history'>('log')
  const [logType, setLogType] = useState<'craving' | 'usage'>('craving')
  const { logs } = useCravingLogs()

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-gray-900">Track</h1>

      <div className="flex gap-2">
        {(['log', 'history'] as const).map((tab) => (
          <button
            key={tab}
            onClick={() => setActiveTab(tab)}
            className={`px-4 py-2 rounded-lg font-medium capitalize transition-colors ${activeTab === tab ? 'bg-green-600 text-white' : 'bg-white text-gray-600 hover:bg-gray-50'}`}
          >
            {tab}
          </button>
        ))}
      </div>

      {activeTab === 'log' && (
        <div className="bg-white rounded-2xl p-6 shadow-sm">
          <div className="flex gap-2 mb-6">
            {(['craving', 'usage'] as const).map((t) => (
              <button
                key={t}
                onClick={() => setLogType(t)}
                className={`px-4 py-2 rounded-lg font-medium capitalize ${logType === t ? 'bg-red-100 text-red-700' : 'text-gray-500 hover:bg-gray-50'}`}
              >
                {t === 'craving' ? '⚡ Log Craving' : '📝 Log Use'}
              </button>
            ))}
          </div>
          {logType === 'craving' ? <CravingLogForm /> : <UsageLogForm />}
        </div>
      )}

      {activeTab === 'history' && (
        <div className="space-y-3">
          {(logs ?? []).map((log) => (
            <div key={log.id} className="bg-white rounded-xl p-4 shadow-sm flex items-center gap-4">
              <div className={`w-3 h-3 rounded-full ${log.triggered ? 'bg-red-400' : 'bg-green-400'}`} />
              <div className="flex-1">
                <div className="font-medium text-gray-900">{log.intensity} craving</div>
                <div className="text-sm text-gray-500">{formatDistanceToNow(new Date(log.loggedAt))} ago</div>
              </div>
              <div className={`text-sm font-medium ${log.triggered ? 'text-red-600' : 'text-green-600'}`}>
                {log.triggered ? 'Used' : 'Beat it'}
              </div>
            </div>
          ))}
          {(logs ?? []).length === 0 && (
            <div className="text-center py-12 text-gray-500">No cravings logged yet. Start logging to see your patterns.</div>
          )}
        </div>
      )}
    </div>
  )
}
