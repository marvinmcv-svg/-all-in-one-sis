'use client'

import useSWR from 'swr'
import Link from 'next/link'
import { useParams } from 'next/navigation'
import { useState, useEffect, useRef } from 'react'

const fetcher = (url: string) => fetch(url).then((r) => r.json())

interface Lesson {
  weekNumber: number
  lessonNumber: number
  title: string
  content: string
  exerciseType: string
  completedAt: string | null
  aiFeedback: string | null
  responseText: string | null
}

const PLACEHOLDERS: Record<string, string> = {
  THOUGHT_RECORD: 'Describe the situation, your automatic thought, and the emotion it caused...',
  BEHAVIORAL_ACTIVATION: 'What behavioral change are you committing to?',
  EXPOSURE: 'Describe the exposure situation and how you plan to approach it...',
  RELAXATION: 'How did the relaxation technique feel? What did you notice?',
  MINDFULNESS: 'What did you observe during this mindfulness practice?',
  REFLECTION: 'Reflect on this topic and what it means for your recovery...',
}

export default function CBTLessonPage() {
  const params = useParams()
  const week = parseInt(params.week as string, 10)
  const lesson = parseInt(params.lesson as string, 10)

  const { data, mutate } = useSWR<{ data: Lesson[] }>('/api/v1/cbt/program', fetcher)
  const lessons = data?.data ?? []

  const lessonIndex = (week - 1) * 7 + (lesson - 1)
  const entry = lessons[lessonIndex] ?? null

  const [responseText, setResponseText] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const [submitted, setSubmitted] = useState(false)
  const [aiFeedback, setAiFeedback] = useState<string | null>(null)

  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null)
  const pollStartRef = useRef<number | null>(null)

  useEffect(() => {
    if (entry?.responseText) {
      setResponseText(entry.responseText)
    }
    if (entry?.aiFeedback) {
      setAiFeedback(entry.aiFeedback)
    }
  }, [entry?.responseText, entry?.aiFeedback])

  const stopPolling = () => {
    if (pollRef.current) {
      clearInterval(pollRef.current)
      pollRef.current = null
    }
  }

  useEffect(() => {
    return () => stopPolling()
  }, [])

  const startPolling = () => {
    pollStartRef.current = Date.now()
    pollRef.current = setInterval(async () => {
      if (Date.now() - (pollStartRef.current ?? 0) > 30000) {
        stopPolling()
        return
      }
      const freshData = await mutate()
      const freshLesson = freshData?.data?.[lessonIndex]
      if (freshLesson?.aiFeedback) {
        setAiFeedback(freshLesson.aiFeedback)
        stopPolling()
      }
    }, 3000)
  }

  const handleSubmit = async () => {
    if (!responseText.trim() || !entry) return
    setSubmitting(true)
    try {
      await fetch(`/api/v1/cbt/${lessonIndex}/complete`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ responseText }),
      })
      setSubmitted(true)
      setAiFeedback(null)
      startPolling()
      await mutate()
    } finally {
      setSubmitting(false)
    }
  }

  const nextWeek = lesson === 7 ? week + 1 : week
  const nextLesson = lesson === 7 ? 1 : lesson + 1
  const hasNext = !(week === 6 && lesson === 7)

  if (!entry && lessons.length > 0) {
    return (
      <div className="space-y-6">
        <Link href="/dashboard/cbt" className="inline-flex items-center gap-1 text-sm text-gray-500 hover:text-gray-700">
          ← Back
        </Link>
        <div className="bg-white rounded-2xl p-6 shadow-sm text-center text-gray-500">
          Lesson not found.
        </div>
      </div>
    )
  }

  if (!entry) {
    return (
      <div className="space-y-6">
        <Link href="/dashboard/cbt" className="inline-flex items-center gap-1 text-sm text-gray-500 hover:text-gray-700">
          ← Back
        </Link>
        <div className="bg-white rounded-2xl p-8 shadow-sm text-center text-gray-400 text-sm">
          Loading lesson...
        </div>
      </div>
    )
  }

  const placeholder = PLACEHOLDERS[entry.exerciseType] ?? 'Write your response...'
  const alreadyCompleted = !!entry.completedAt

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <Link href="/dashboard/cbt" className="inline-flex items-center gap-1 text-sm text-gray-500 hover:text-gray-700">
          ← Back
        </Link>
        {hasNext && (
          <Link
            href={`/dashboard/cbt/${nextWeek}/${nextLesson}`}
            className="inline-flex items-center gap-1 text-sm font-medium text-green-600 hover:text-green-700"
          >
            Next Lesson →
          </Link>
        )}
      </div>

      <div className="bg-white rounded-2xl p-6 shadow-sm space-y-2">
        <div className="flex items-center gap-2">
          <span className="text-xs font-medium text-green-600 bg-green-50 px-2 py-1 rounded-full">
            Week {week} · Lesson {lesson}
          </span>
          {alreadyCompleted && (
            <span className="text-xs font-medium text-white bg-green-500 px-2 py-1 rounded-full">
              ✓ Completed
            </span>
          )}
        </div>
        <h1 className="text-2xl font-bold text-gray-900">{entry.title}</h1>
      </div>

      <div className="bg-white rounded-2xl p-6 shadow-sm">
        <h2 className="text-sm font-semibold text-gray-500 uppercase tracking-wide mb-3">Lesson Content</h2>
        <p className="text-gray-700 text-sm leading-relaxed whitespace-pre-wrap">{entry.content}</p>
      </div>

      {alreadyCompleted && entry.responseText && !submitted && (
        <div className="bg-white rounded-2xl p-6 shadow-sm">
          <h2 className="text-sm font-semibold text-gray-500 uppercase tracking-wide mb-3">Your Previous Response</h2>
          <p className="text-gray-700 text-sm leading-relaxed whitespace-pre-wrap">{entry.responseText}</p>
          {entry.aiFeedback && (
            <div className="mt-4 p-4 bg-green-50 rounded-xl border border-green-100">
              <h3 className="text-sm font-semibold text-green-700 mb-1">AI Feedback</h3>
              <p className="text-green-800 text-sm leading-relaxed">{entry.aiFeedback}</p>
            </div>
          )}
        </div>
      )}

      {submitted ? (
        <div className="bg-white rounded-2xl p-6 shadow-sm space-y-4">
          <div className="text-center py-4">
            <div className="text-4xl mb-2">🎉</div>
            <h2 className="text-xl font-bold text-gray-900">Great work!</h2>
            <p className="text-gray-500 text-sm mt-1">Your response has been saved.</p>
          </div>
          {aiFeedback ? (
            <div className="p-4 bg-green-50 rounded-xl border border-green-100">
              <h3 className="text-sm font-semibold text-green-700 mb-1">AI Feedback</h3>
              <p className="text-green-800 text-sm leading-relaxed">{aiFeedback}</p>
            </div>
          ) : (
            <div className="flex items-center gap-2 text-sm text-gray-400 justify-center">
              <svg className="animate-spin w-4 h-4 text-green-500" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z" />
              </svg>
              Generating AI feedback...
            </div>
          )}
        </div>
      ) : (
        <div className="bg-white rounded-2xl p-6 shadow-sm space-y-4">
          <h2 className="text-sm font-semibold text-gray-500 uppercase tracking-wide">
            {alreadyCompleted ? 'Resubmit Your Response' : 'Your Response'}
          </h2>
          <textarea
            value={responseText}
            onChange={(e) => setResponseText(e.target.value)}
            placeholder={placeholder}
            rows={6}
            className="w-full p-3 border border-gray-200 rounded-xl text-sm leading-relaxed resize-none focus:outline-none focus:ring-2 focus:ring-green-500"
          />
          <button
            onClick={handleSubmit}
            disabled={!responseText.trim() || submitting}
            className="w-full py-3 bg-green-600 text-white rounded-xl font-medium hover:bg-green-700 disabled:opacity-50 transition-colors"
          >
            {submitting ? 'Submitting...' : alreadyCompleted ? 'Resubmit Response' : 'Submit Response'}
          </button>
        </div>
      )}
    </div>
  )
}
