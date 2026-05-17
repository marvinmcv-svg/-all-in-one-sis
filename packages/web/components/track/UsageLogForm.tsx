'use client'

import { useState } from 'react'
import { TriggerPicker } from './TriggerPicker'

export function UsageLogForm() {
  const [amount, setAmount] = useState(1)
  const [mood, setMood] = useState(5)
  const [tags, setTags] = useState<string[]>([])
  const [notes, setNotes] = useState('')
  const [loading, setLoading] = useState(false)
  const [done, setDone] = useState(false)

  const handleSubmit = async () => {
    setLoading(true)
    try {
      await fetch('/api/v1/usage', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ substanceType: 'NICOTINE', amount, mood, triggerTags: tags, notes: notes || null }),
      })
      setDone(true)
    } finally {
      setLoading(false)
    }
  }

  if (done) return <div className="text-center py-8 text-green-600 font-medium">✓ Logged. No shame — just data.</div>

  return (
    <div className="space-y-4">
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">Amount (puffs/sessions)</label>
        <input type="number" min={1} value={amount} onChange={(e) => setAmount(parseInt(e.target.value))} className="w-full p-3 border border-gray-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-green-500" />
      </div>
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">Mood: {mood}/10</label>
        <input type="range" min={1} max={10} value={mood} onChange={(e) => setMood(parseInt(e.target.value))} className="w-full accent-green-600" />
      </div>
      <TriggerPicker selected={tags} onChange={setTags} />
      <textarea value={notes} onChange={(e) => setNotes(e.target.value)} rows={2} placeholder="Notes (optional)" className="w-full p-3 border border-gray-200 rounded-xl text-sm resize-none" />
      <button onClick={handleSubmit} disabled={loading} className="w-full py-3 bg-red-500 text-white rounded-xl font-semibold hover:bg-red-600 disabled:opacity-50">
        {loading ? 'Logging...' : 'Log Use (no shame)'}
      </button>
    </div>
  )
}
