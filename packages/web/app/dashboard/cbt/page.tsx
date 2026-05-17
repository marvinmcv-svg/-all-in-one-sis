'use client'

import useSWR from 'swr'
import Link from 'next/link'
import { ProgressRing } from '@/components/cbt/ProgressRing'

const fetcher = (url: string) => fetch(url).then((r) => r.json())

export default function CBTProgramPage() {
  const { data: progress } = useSWR('/api/v1/cbt/progress', fetcher)
  const { data: program } = useSWR('/api/v1/cbt/program', fetcher)

  const lessons = program?.data ?? []
  const weeks = [1, 2, 3, 4, 5, 6]

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-900">CBT Program</h1>
        {progress?.data && (
          <div className="flex items-center gap-3">
            <ProgressRing progress={progress.data.percentComplete} />
            <div>
              <div className="font-semibold">{progress.data.completedLessons}/{progress.data.totalLessons} lessons</div>
              <div className="text-sm text-gray-500">Week {progress.data.currentWeek} of 6</div>
            </div>
          </div>
        )}
      </div>

      <div className="space-y-4">
        {weeks.map((week) => {
          const weekLessons = lessons.filter((l: { weekNumber: number }) => l.weekNumber === week)
          const completed = weekLessons.filter((l: { completedAt: string | null }) => l.completedAt).length
          return (
            <div key={week} className="bg-white rounded-2xl p-6 shadow-sm">
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-lg font-semibold text-gray-900">Week {week}</h2>
                <span className="text-sm text-gray-500">{completed}/{weekLessons.length} done</span>
              </div>
              <div className="w-full bg-gray-100 rounded-full h-2 mb-4">
                <div
                  className="bg-green-500 h-2 rounded-full transition-all"
                  style={{ width: `${weekLessons.length > 0 ? (completed / weekLessons.length) * 100 : 0}%` }}
                />
              </div>
              <div className="space-y-2">
                {weekLessons.map((lesson: { lessonNumber: number; title: string; completedAt: string | null }) => (
                  <Link
                    key={lesson.lessonNumber}
                    href={`/dashboard/cbt/${week}/${lesson.lessonNumber}`}
                    className="flex items-center gap-3 p-3 rounded-lg hover:bg-gray-50 transition-colors"
                  >
                    <div className={`w-6 h-6 rounded-full flex items-center justify-center text-xs ${lesson.completedAt ? 'bg-green-500 text-white' : 'bg-gray-200 text-gray-500'}`}>
                      {lesson.completedAt ? '✓' : lesson.lessonNumber}
                    </div>
                    <span className={lesson.completedAt ? 'text-gray-500 line-through' : 'text-gray-900'}>{lesson.title}</span>
                  </Link>
                ))}
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}
