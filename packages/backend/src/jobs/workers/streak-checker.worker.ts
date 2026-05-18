import { Worker, Job } from 'bullmq'
import { db, users, cravingLogs, usageLogs } from '@clearpath/db'
import { eq, gte, and } from 'drizzle-orm'
import { pushNotificationsQueue, badgeEvaluatorQueue } from '../index.js'

export interface StreakCheckerPayload {
  userId?: string // if undefined, process all users
}

async function checkStreakForUser(userId: string): Promise<void> {
  const [user] = await db.select().from(users).where(eq(users.id, userId)).limit(1)
  if (!user || !user.quitDate) return

  const daysClean = Math.floor((Date.now() - user.quitDate.getTime()) / 86400000)

  // Update longest streak if needed
  if (daysClean > (user.longestStreakDays ?? 0)) {
    await db.update(users)
      .set({ longestStreakDays: daysClean, updatedAt: new Date() })
      .where(eq(users.id, userId))
  }

  // Check if user has logged anything today
  const todayStart = new Date()
  todayStart.setHours(0, 0, 0, 0)

  const [todayCravingLog] = await db.select().from(cravingLogs)
    .where(and(eq(cravingLogs.userId, userId), gte(cravingLogs.loggedAt, todayStart)))
    .limit(1)

  const [todayUsageLog] = await db.select().from(usageLogs)
    .where(and(eq(usageLogs.userId, userId), gte(usageLogs.loggedAt, todayStart)))
    .limit(1)

  const hasLoggedToday = !!todayCravingLog || !!todayUsageLog

  // Send streak alert if they have a streak but haven't logged today
  if (!hasLoggedToday && daysClean > 0 && user.expoPushToken && user.notificationsEnabled) {
    await pushNotificationsQueue.add('streak-alert', {
      token: user.expoPushToken,
      title: `🔥 ${daysClean}-day streak on the line`,
      body: `You haven't logged today — don't break your ${daysClean}-day streak! Tap to log.`,
      data: { type: 'STREAK_ALERT', screen: 'track' },
    })
  }

  // Evaluate badges (streak milestones)
  await badgeEvaluatorQueue.add('evaluate', { userId })
}

const redisConnection = {
  host: process.env['UPSTASH_REDIS_HOST'] ?? 'localhost',
  port: parseInt(process.env['UPSTASH_REDIS_PORT'] ?? '6379'),
  password: process.env['UPSTASH_REDIS_PASSWORD'],
  tls: process.env['NODE_ENV'] === 'production' ? {} : undefined,
}

export const streakCheckerWorker = new Worker<StreakCheckerPayload>(
  'streak-checker',
  async (job: Job<StreakCheckerPayload>) => {
    if (job.data.userId) {
      await checkStreakForUser(job.data.userId)
      return
    }

    // Process all users who have notifications enabled and a quit date
    const allUsers = await db.select({ id: users.id })
      .from(users)
      .where(eq(users.notificationsEnabled, true))

    await Promise.allSettled(allUsers.map((u) => checkStreakForUser(u.id)))
    return { processed: allUsers.length }
  },
  { connection: redisConnection, concurrency: 1 }
)

streakCheckerWorker.on('failed', (job, err) => {
  console.error(`Streak checker job ${job?.id} failed:`, err)
})
