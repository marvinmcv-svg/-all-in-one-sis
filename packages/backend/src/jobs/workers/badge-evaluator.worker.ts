import { Worker, Job } from 'bullmq'
import { db, users, badges, cravingLogs, usageLogs, cbtModules, communityPosts, nicotineProfiles } from '@clearpath/db'
import { eq, and, count, gte } from 'drizzle-orm'
import { BADGE_DEFINITIONS, pushNotificationsQueue } from '../index.js'

export interface BadgeEvaluatorPayload {
  userId: string
}

export async function evaluateBadgesForUser(userId: string): Promise<string[]> {
  const [user] = await db.select().from(users).where(eq(users.id, userId)).limit(1)
  if (!user) return []

  // Fetch already-earned badge keys
  const earnedRows = await db.select({ badgeKey: badges.badgeKey }).from(badges).where(eq(badges.userId, userId))
  const earned = new Set(earnedRows.map((r) => r.badgeKey))

  const newBadges: string[] = []

  // Calculate days clean
  const daysClean = user.quitDate
    ? Math.floor((Date.now() - user.quitDate.getTime()) / 86400000)
    : 0

  // Calculate money saved
  const [nicProfile] = await db.select().from(nicotineProfiles).where(eq(nicotineProfiles.userId, userId)).limit(1)
  const dailyCost = nicProfile ? nicProfile.costPerUnit * nicProfile.dailyUsageAmount : 0
  const moneySavedCents = Math.round(daysClean * dailyCost * 100)

  // Count beaten cravings
  const [beatenResult] = await db
    .select({ value: count() })
    .from(cravingLogs)
    .where(and(eq(cravingLogs.userId, userId), eq(cravingLogs.triggered, false)))
  const cravingsBeaten = beatenResult?.value ?? 0

  // Count completed CBT weeks
  const completedModules = await db.select().from(cbtModules)
    .where(and(eq(cbtModules.userId, userId)))
  const cbtWeeksCompleted = completedModules.filter((m) => m.completedAt !== null && m.weekNumber === 1 && m.lessonNumber === 7).length > 0 ? 1 : 0

  // Count community posts
  const [postCountResult] = await db
    .select({ value: count() })
    .from(communityPosts)
    .where(eq(communityPosts.authorId, userId))
  const postCount = postCountResult?.value ?? 0

  // Check streak (days since last usage log, or days clean)
  const streakDays = daysClean

  for (const def of BADGE_DEFINITIONS) {
    if (earned.has(def.key)) continue

    let qualifies = false

    if (def.category === 'TIME_CLEAN' && 'targetDays' in def) {
      qualifies = daysClean >= def.targetDays
    } else if (def.category === 'MONEY_SAVED' && 'targetCents' in def) {
      qualifies = moneySavedCents >= def.targetCents
    } else if (def.category === 'CRAVINGS_BEATEN' && 'count' in def) {
      qualifies = cravingsBeaten >= def.count
    } else if (def.category === 'CBT_PROGRESS' && 'weeks' in def) {
      qualifies = cbtWeeksCompleted >= def.weeks
    } else if (def.category === 'STREAK' && 'days' in def) {
      qualifies = streakDays >= def.days
    } else if (def.category === 'COMMUNITY' && 'posts' in def) {
      qualifies = postCount >= def.posts
    }

    if (qualifies) {
      try {
        await db.insert(badges).values({
          userId,
          badgeKey: def.key,
          category: def.category,
          title: def.title,
          description: def.description,
          iconEmoji: def.emoji,
        })
        newBadges.push(def.key)

        // Queue push notification for badge earned
        if (user.expoPushToken && user.notificationsEnabled) {
          await pushNotificationsQueue.add('badge-earned', {
            token: user.expoPushToken,
            title: `${def.emoji} New Badge: ${def.title}`,
            body: def.description,
            data: { type: 'BADGE_EARNED', screen: 'badges', badgeKey: def.key },
          })
        }
      } catch {
        // Badge already exists (race condition) — ignore unique constraint violation
      }
    }
  }

  if (newBadges.length > 0) {
    await db.update(users)
      .set({ totalBadgesEarned: (user.totalBadgesEarned ?? 0) + newBadges.length })
      .where(eq(users.id, userId))
  }

  return newBadges
}

const redisConnection = {
  host: process.env['UPSTASH_REDIS_HOST'] ?? 'localhost',
  port: parseInt(process.env['UPSTASH_REDIS_PORT'] ?? '6379'),
  password: process.env['UPSTASH_REDIS_PASSWORD'],
  tls: process.env['NODE_ENV'] === 'production' ? {} : undefined,
}

export const badgeEvaluatorWorker = new Worker<BadgeEvaluatorPayload>(
  'badge-evaluator',
  async (job: Job<BadgeEvaluatorPayload>) => {
    const { userId } = job.data
    const awarded = await evaluateBadgesForUser(userId)
    return { userId, awarded }
  },
  { connection: redisConnection, concurrency: 5 }
)

badgeEvaluatorWorker.on('failed', (job, err) => {
  console.error(`Badge evaluator job ${job?.id} failed:`, err)
})
