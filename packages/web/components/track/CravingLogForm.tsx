'use client'

import { useState } from 'react'
import { TriggerPicker } from './TriggerPicker'

interface Props {
  onSuccess?: () => void
}

export function CravingLogForm({ onSuccess }: Props) {
  const [intensity, setIntensity] = useState<'LOW' | 'MEDIUM' | 'HIGH' | 'OVERWHELMING'>('MEDIUM')
  const [triggered, setTriggered] = useState(false)
  const [mood, setMood] = useState(5)
  const [tags, setTags] = useState<string[]>([])
  const [notes, setNotes] = useState('')
  const [loading, setLoading] = useState(false)

  const handleSubmit = async () => {
    setLoading(true)
    try {
      await fetch('/api/v1/cravings', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ substanceType: 'NICOTINE', intensity, triggered, triggerTags: tags, mood, notes: notes || null }),
      })
      onSuccess?.()
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="space-y-4">
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">Intensity</label>
        <div className="grid grid-cols-4 gap-2">
          {(['LOW', 'MEDIUM', 'HIGH', 'OVERWHELMING'] as const).map((i) => (
            <button
              key={i}
              onClick={() => setIntensity(i)}
              className={`py-2 px-2 rounded-lg text-xs font-medium border-2 transition-colors ${intensity === i ? 'border-green-500 bg-green-50 text-green-700' : 'border-gray-200'}`}
            >
              {i}
            </button>
          ))}
        </div>
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">Did you use?</label>
        <div className="flex gap-3">
          <button onClick={() => setTriggered(false)} className={`flex-1 py-2 rounded-lg border-2 font-medium text-sm ${!triggered ? 'border-green-500 bg-green-50 text-green-700' : 'border-gray-200'}`}>Beat it 💪</button>
          <button onClick={() => setTriggered(true)} className={`flex-1 py-2 rounded-lg border-2 font-medium text-sm ${triggered ? 'border-red-400 bg-red-50 text-red-700' : 'border-gray-200'}`}>Used 😔</button>
        </div>
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">Mood: {mood}/10</label>
        <input type="range" min={1} max={10} value={mood} onChange={(e) => setMood(parseInt(e.target.value))} className="w-full accent-green-600" />
      </div>

      <TriggerPicker selected={tags} onChange={setTags} />

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">Notes (optional)</label>
        <textarea value={notes} onChange={(e) => setNotes(e.target.value)} rows={2} placeholder="What happened?" className="w-full p-3 border border-gray-200 rounded-xl text-sm resize-none focus:outline-none focus:ring-2 focus:ring-green-500" />
      </div>

      <button onClick={handleSubmit} disabled={loading} className="w-full py-3 bg-green-600 text-white rounded-xl font-semibold hover:bg-green-700 disabled:opacity-50">
        {loading ? 'Logging...' : 'Log Craving'}
      </button>
    </div>
  )
}
