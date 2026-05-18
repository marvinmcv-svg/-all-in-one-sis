'use client'

import useSWR from 'swr'
import Link from 'next/link'
import { formatDistanceToNow } from 'date-fns'
import { useState } from 'react'

const fetcher = (url: string) => fetch(url).then((r) => r.json())

interface JournalEntry {
  id: string
  title: string | null
  content: string
  mood: number
  createdAt: string
}

export default function JournalPage() {
  const { data, mutate } = useSWR<{ data: JournalEntry[] }>('/api/v1/journal', fetcher)
  const entries = data?.data ?? []
  const [showForm, setShowForm] = useState(false)
  const [title, setTitle] = useState('')
  const [content, setContent] = useState('')
  const [mood, setMood] = useState(5)
  const [saving, setSaving] = useState(false)

  const handleSave = async () => {
    setSaving(true)
    try {
      await fetch('/api/v1/journal', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ title: title || null, content, mood }),
      })
      setTitle('')
      setContent('')
      setMood(5)
      setShowForm(false)
      await mutate()
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-900">Journal</h1>
        <button
          onClick={() => setShowForm(!showForm)}
          className="px-4 py-2 bg-green-600 text-white rounded-xl font-medium hover:bg-green-700"
        >
          + New Entry
        </button>
      </div>

      {showForm && (
        <div className="bg-white rounded-2xl p-6 shadow-sm space-y-4">
          <input
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            placeholder="Title (optional)"
            className="w-full text-xl font-semibold border-b border-gray-100 pb-3 focus:outline-none"
          />
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Mood: {mood}/10</label>
            <input type="range" min={1} max={10} value={mood} onChange={(e) => setMood(parseInt(e.target.value))} className="w-full accent-green-600" />
          </div>
          <textarea
            value={content}
            onChange={(e) => setContent(e.target.value)}
            placeholder="How are you feeling? What's on your mind?"
            rows={6}
            autoFocus
            className="w-full text-gray-700 text-sm leading-relaxed resize-none focus:outline-none"
          />
          <div className="flex gap-3">
            <button onClick={() => setShowForm(false)} className="flex-1 py-2 border-2 border-gray-200 rounded-xl text-sm font-medium">Cancel</button>
            <button
              onClick={handleSave}
              disabled={!content.trim() || saving}
              className="flex-1 py-2 bg-green-600 text-white rounded-xl text-sm font-medium disabled:opacity-50"
            >
              {saving ? 'Saving...' : 'Save Entry'}
            </button>
          </div>
        </div>
      )}

      <div className="space-y-4">
        {entries.map((entry) => (
          <Link key={entry.id} href={`/dashboard/journal/${entry.id}`} className="block bg-white rounded-2xl p-6 shadow-sm hover:shadow-md transition-shadow">
            <div className="flex items-center gap-2 mb-2">
              <span className="text-xs text-gray-400">{formatDistanceToNow(new Date(entry.createdAt))} ago</span>
              <span className="text-xs bg-gray-100 px-2 py-0.5 rounded-full text-gray-600">Mood {entry.mood}/10</span>
            </div>
            <h3 className="text-lg font-semibold text-gray-900 mb-1">{entry.title ?? 'Untitled'}</h3>
            <p className="text-gray-600 text-sm leading-relaxed line-clamp-2">{entry.content}</p>
          </Link>
        ))}
        {entries.length === 0 && (
          <div className="text-center py-16 text-gray-500">
            <div className="text-4xl mb-3">📓</div>
            <div className="font-medium">No journal entries yet</div>
            <div className="text-sm mt-1">Start writing to track your emotional journey</div>
          </div>
        )}
      </div>
    </div>
  )
}
