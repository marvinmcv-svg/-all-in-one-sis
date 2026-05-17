'use client'

import useSWR from 'swr'

const fetcher = (url: string) => fetch(url).then((r) => r.json())

interface EarnedBadge {
  badgeKey: string
  earnedAt: string
}

const ALL_BADGES = [
  { key: 'day_1', emoji: '🌱', title: '24 Hours', desc: 'One full day clean', category: 'Time' },
  { key: 'day_3', emoji: '🌿', title: 'Three Days', desc: 'Three days clean', category: 'Time' },
  { key: 'week_1', emoji: '🌳', title: 'One Week', desc: 'One full week clean', category: 'Time' },
  { key: 'week_2', emoji: '💪', title: 'Two Weeks', desc: 'Two weeks clean', category: 'Time' },
  { key: 'month_1', emoji: '🏆', title: 'One Month', desc: 'One month clean', category: 'Time' },
  { key: 'month_3', emoji: '💎', title: 'Three Months', desc: 'Three months clean', category: 'Time' },
  { key: 'month_6', emoji: '🌟', title: 'Six Months', desc: 'Six months clean', category: 'Time' },
  { key: 'year_1', emoji: '👑', title: 'One Year', desc: 'One full year clean', category: 'Time' },
  { key: 'saved_50', emoji: '💰', title: '$50 Saved', desc: 'Saved $50 since quitting', category: 'Money' },
  { key: 'saved_100', emoji: '💵', title: '$100 Saved', desc: 'Saved $100 since quitting', category: 'Money' },
  { key: 'cbt_week1', emoji: '🧠', title: 'CBT Week 1', desc: 'Completed CBT Week 1', category: 'CBT' },
  { key: 'craving_5', emoji: '⚡', title: 'Beat 5', desc: 'Beat 5 cravings total', category: 'Cravings' },
  { key: 'craving_25', emoji: '🛡️', title: '25 Beaten', desc: 'Beat 25 cravings total', category: 'Cravings' },
  { key: 'streak_7', emoji: '🔥', title: '7-Day Streak', desc: '7 consecutive days logged', category: 'Streak' },
  { key: 'first_post', emoji: '💬', title: 'First Post', desc: 'Made first community post', category: 'Community' },
]

export default function BadgesPage() {
  const { data } = useSWR<{ data: EarnedBadge[] }>('/api/v1/dashboard/badges', fetcher)
  const earned = data?.data ?? []
  const earnedKeys = new Set(earned.map((b) => b.badgeKey))

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Badges</h1>
        <p className="text-gray-500 text-sm mt-1">{earnedKeys.size} / {ALL_BADGES.length} earned</p>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
        {ALL_BADGES.map((badge) => {
          const isEarned = earnedKeys.has(badge.key)
          return (
            <div
              key={badge.key}
              className={`bg-white rounded-2xl p-6 text-center shadow-sm transition-all duration-300 ${
                isEarned ? 'ring-2 ring-green-400 shadow-green-100' : 'opacity-40 grayscale'
              }`}
            >
              <div className={`text-4xl mb-3 transition-transform ${isEarned ? 'scale-110' : ''}`}>
                {badge.emoji}
              </div>
              <div className="font-semibold text-gray-900 mb-1 text-sm">{badge.title}</div>
              <div className="text-xs text-gray-500 leading-snug">{badge.desc}</div>
              {isEarned ? (
                <div className="mt-3 text-xs text-green-600 font-medium bg-green-50 rounded-full px-2 py-0.5">
                  ✓ Earned
                </div>
              ) : (
                <div className="mt-3 text-xs text-gray-400">Locked</div>
              )}
            </div>
          )
        })}
      </div>
    </div>
  )
}
