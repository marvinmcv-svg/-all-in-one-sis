'use client'

import useSWR from 'swr'
import Link from 'next/link'
import { useParams, useRouter } from 'next/navigation'
import { useState, useEffect } from 'react'
import { format } from 'date-fns'

const fetcher = (url: string) => fetch(url).then((r) => r.json())

interface JournalEntry {
  id: string
  title: string | null
  content: string
  mood: number
  createdAt: string
}

export default function JournalEntryPage() {
  const params = useParams()
  const router = useRouter()
  const id = params.id as string

  const { data, mutate } = useSWR<{ data: JournalEntry }>(`/api/v1/journal/${id}`, fetcher)
  const entry = data?.data ?? null

  const [editing, setEditing] = useState(false)
  const [editTitle, setEditTitle] = useState('')
  const [editContent, setEditContent] = useState('')
  const [editMood, setEditMood] = useState(5)
  const [saving, setSaving] = useState(false)
  const [deleting, setDeleting] = useState(false)
  const [confirmDelete, setConfirmDelete] = useState(false)

  useEffect(() => {
    if (entry) {
      setEditTitle(entry.title ?? '')
      setEditContent(entry.content)
      setEditMood(entry.mood)
    }
  }, [entry?.id])

  const handleSave = async () => {
    if (!entry) return
    setSaving(true)
    try {
      await fetch(`/api/v1/journal/${id}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ title: editTitle || null, content: editContent, mood: editMood }),
      })
      await mutate()
      setEditing(false)
    } finally {
      setSaving(false)
    }
  }

  const handleDelete = async () => {
    setDeleting(true)
    try {
      await fetch(`/api/v1/journal/${id}`, { method: 'DELETE' })
      router.push('/dashboard/journal')
    } finally {
      setDeleting(false)
    }
  }

  if (!entry) {
    return (
      <div className="space-y-6">
        <Link href="/dashboard/journal" className="inline-flex items-center gap-1 text-sm text-gray-500 hover:text-gray-700">
          ← Back
        </Link>
        <div className="bg-white rounded-2xl p-8 shadow-sm text-center text-gray-400 text-sm">
          Loading entry...
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <Link href="/dashboard/journal" className="inline-flex items-center gap-1 text-sm text-gray-500 hover:text-gray-700">
          ← Back to Journal
        </Link>
        <div className="flex items-center gap-2">
          {!editing && (
            <button
              onClick={() => setEditing(true)}
              className="px-4 py-2 border-2 border-gray-200 rounded-xl text-sm font-medium hover:border-gray-300 transition-colors"
            >
              Edit
            </button>
          )}
          {!confirmDelete ? (
            <button
              onClick={() => setConfirmDelete(true)}
              className="px-4 py-2 bg-red-50 text-red-600 border-2 border-red-100 rounded-xl text-sm font-medium hover:bg-red-100 transition-colors"
            >
              Delete
            </button>
          ) : (
            <div className="flex items-center gap-2">
              <span className="text-xs text-gray-500">Sure?</span>
              <button
                onClick={handleDelete}
                disabled={deleting}
                className="px-3 py-1.5 bg-red-600 text-white rounded-xl text-sm font-medium hover:bg-red-700 disabled:opacity-50 transition-colors"
              >
                {deleting ? 'Deleting...' : 'Yes, delete'}
              </button>
              <button
                onClick={() => setConfirmDelete(false)}
                className="px-3 py-1.5 border-2 border-gray-200 rounded-xl text-sm font-medium"
              >
                Cancel
              </button>
            </div>
          )}
        </div>
      </div>

      <div className="bg-white rounded-2xl p-6 shadow-sm space-y-4">
        <div className="flex items-center gap-3 text-sm text-gray-400">
          <span>{format(new Date(entry.createdAt), 'MMMM d, yyyy')}</span>
          <span className="bg-gray-100 px-2 py-0.5 rounded-full text-gray-600">
            Mood {editing ? editMood : entry.mood}/10
          </span>
        </div>

        {editing ? (
          <>
            <input
              value={editTitle}
              onChange={(e) => setEditTitle(e.target.value)}
              placeholder="Title (optional)"
              className="w-full text-xl font-semibold border-b border-gray-100 pb-3 focus:outline-none"
            />
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Mood: {editMood}/10
              </label>
              <input
                type="range"
                min={1}
                max={10}
                value={editMood}
                onChange={(e) => setEditMood(parseInt(e.target.value, 10))}
                className="w-full accent-green-600"
              />
            </div>
            <textarea
              value={editContent}
              onChange={(e) => setEditContent(e.target.value)}
              rows={10}
              className="w-full text-gray-700 text-sm leading-relaxed resize-none focus:outline-none border border-gray-200 rounded-xl p-3 focus:ring-2 focus:ring-green-500"
            />
            <div className="flex gap-3">
              <button
                onClick={() => {
                  setEditing(false)
                  setEditTitle(entry.title ?? '')
                  setEditContent(entry.content)
                  setEditMood(entry.mood)
                }}
                className="flex-1 py-2 border-2 border-gray-200 rounded-xl text-sm font-medium"
              >
                Cancel
              </button>
              <button
                onClick={handleSave}
                disabled={!editContent.trim() || saving}
                className="flex-1 py-2 bg-green-600 text-white rounded-xl text-sm font-medium disabled:opacity-50 hover:bg-green-700 transition-colors"
              >
                {saving ? 'Saving...' : 'Save'}
              </button>
            </div>
          </>
        ) : (
          <>
            <h1 className="text-2xl font-bold text-gray-900">
              {entry.title ?? 'Untitled'}
            </h1>
            <p className="text-gray-700 text-sm leading-relaxed whitespace-pre-wrap">
              {entry.content}
            </p>
          </>
        )}
      </div>
    </div>
  )
}
