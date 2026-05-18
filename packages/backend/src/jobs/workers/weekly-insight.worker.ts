import { Worker, Job } from 'bullmq'
import { db, users, cravingLogs, usageLogs } from '@clearpath/db'
import { eq, and, gte } from 'drizzle-orm'
import { pushNotificationsQueue } from '../index.js'
import Anthropic from '@anthropic-ai/sdk'

const anthropic = new Anthropic({ apiKey: process.env['ANTHROPIC_API_KEY'] })

export interface WeeklyInsightPayload {
  userId?: string
}

async function generateInsightForUser(userId: string, redisClient: { set: (k: string, v: string, opts?: Record<string, unknown>) => Promise<unknown> }): Promise<void> {
  const [user] = await db.select().from(users).where(eq(users.id, userId)).limit(1)
  if (!user || user.subscriptionTier === 'FREE') return

  const sevenDaysAgo = new Date(Date.now() - 7 * 24 * 60 * 60 * 1000)

  const weekCravings = await db.select().from(cravingLogs)
    .where(and(eq(cravingLogs.userId, userId), gte(cravingLogs.loggedAt, sevenDaysAgo)))
  const weekUsage = await db.select().from(usageLogs)
    .where(and(eq(usageLogs.userId, userId), gte(usageLogs.loggedAt, sevenDaysAgo)))

  const beaten = weekCravings.filter((c) => !c.triggered).length
  const total = weekCravings.length
  const avgMood = weekCravings.length > 0
    ? (weekCravings.reduce((sum, c) => sum + c.mood, 0) / weekCravings.length).toFixed(1)
    : null
  const usageCount = weekUsage.length
  const daysClean = user.quitDate
    ? Math.floor((Date.now() - user.quitDate.getTime()) / 86400000)
    : 0

  const prompt = `You are reviewing a ClearPath user's recovery week. Summarize in 1–2 warm, encouraging sentences (max 100 words). Do NOT use bullet points.

Week stats:
- Days clean: ${daysClean}
- Cravings this week: ${total} (beat ${beaten}, gave in ${total - beaten})
- Average mood: ${avgMood ?? 'no data'}/10
- Usage events: ${usageCount}

Generate a brief, personal, motivating insight about their week.`

  const msg = await anthropic.messages.create({
    model: 'claude-sonnet-4-20250514',
    max_tokens: 150,
    messages: [{ role: 'user', content: prompt }],
  })

  const insight = msg.content[0]?.type === 'text' ? msg.content[0].text : 'Keep going — every day clean is a victory.'

  // Cache for 24h
  await redisClient.set(`weekly-insight:${userId}`, JSON.stringify({ insight, generatedAt: new Date().toISOString() }), { ex: 86400 })

  // Send push notification
  if (user.expoPushToken && user.notificationsEnabled) {
    await pushNotificationsQueue.add('weekly-insight', {
      token: user.expoPushToken,
      title: '📊 Your week in review',
      body: insight,
      data: { type: 'WEEKLY_INSIGHT', screen: 'dashboard' },
    })
  }
}

const redisConnection = {
  host: process.env['UPSTASH_REDIS_HOST'] ?? 'localhost',
  port: parseInt(process.env['UPSTASH_REDIS_PORT'] ?? '6379'),
  password: process.env['UPSTASH_REDIS_PASSWORD'],
  tls: process.env['NODE_ENV'] === 'production' ? {} : undefined,
}

export const weeklyInsightWorker = new Worker<WeeklyInsightPayload>(
  'weekly-insight',
  async (job: Job<WeeklyInsightPayload>) => {
    const { Redis } = await import('@upstash/redis')
    const redis = new Redis({
      url: process.env['UPSTASH_REDIS_REST_URL']!,
      token: process.env['UPSTASH_REDIS_REST_TOKEN']!,
    })

    if (job.data.userId) {
      await generateInsightForUser(job.data.userId, redis)
      return
    }

    const premiumUsers = await db.select({ id: users.id })
      .from(users)
      .where(eq(users.subscriptionTier, 'PREMIUM'))

    for (const u of premiumUsers) {
      await generateInsightForUser(u.id, redis)
    }

    return { processed: premiumUsers.length }
  },
  { connection: redisConnection, concurrency: 1 }
)

weeklyInsightWorker.on('failed', (job, err) => {
  console.error(`Weekly insight job ${job?.id} failed:`, err)
})
