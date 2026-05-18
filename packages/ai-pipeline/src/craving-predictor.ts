import type { DB } from '@clearpath/db'
import { cravingLogs } from '@clearpath/db'
import { desc, eq, gte, and } from 'drizzle-orm'

interface PredictionResult {
  willCrave: boolean
  confidence: number
  estimatedWindowStart: Date
  estimatedWindowEnd: Date
  triggerFactors: string[]
}

export async function predictNextCraving(
  db: DB,
  userId: string,
  substanceType: 'NICOTINE' | 'CANNABIS' | 'BOTH'
): Promise<PredictionResult | null> {
  const thirtyDaysAgo = new Date(Date.now() - 30 * 24 * 60 * 60 * 1000)

  const logs = await db
    .select()
    .from(cravingLogs)
    .where(
      and(
        eq(cravingLogs.userId, userId),
        eq(cravingLogs.substanceType, substanceType),
        gte(cravingLogs.loggedAt, thirtyDaysAgo)
      )
    )
    .orderBy(desc(cravingLogs.loggedAt))
    .limit(200)

  if (logs.length < 5) return null

  const hourCounts: Record<number, number> = {}
  const triggerCounts: Record<string, number> = {}

  for (const log of logs) {
    const d = new Date(log.loggedAt)
    const h = d.getHours()
    hourCounts[h] = (hourCounts[h] ?? 0) + 1
    for (const tag of (log.triggerTags as string[])) {
      triggerCounts[tag] = (triggerCounts[tag] ?? 0) + 1
    }
  }

  const peakHour = parseInt(
    Object.entries(hourCounts).sort((a, b) => b[1] - a[1])[0]?.[0] ?? '0'
  )
  const now = new Date()
  const todayPeakHour = new Date(now)
  todayPeakHour.setHours(peakHour, 0, 0, 0)
  if (todayPeakHour <= now) todayPeakHour.setDate(todayPeakHour.getDate() + 1)

  const confidence = Math.min(0.95, logs.length / 100 + 0.3)

  const topTriggers = Object.entries(triggerCounts)
    .sort((a, b) => b[1] - a[1])
    .slice(0, 3)
    .map(([tag]) => tag)

  const windowStart = new Date(todayPeakHour.getTime() - 30 * 60 * 1000)
  const windowEnd = new Date(todayPeakHour.getTime() + 30 * 60 * 1000)

  return {
    willCrave: true,
    confidence,
    estimatedWindowStart: windowStart,
    estimatedWindowEnd: windowEnd,
    triggerFactors: topTriggers,
  }
}
