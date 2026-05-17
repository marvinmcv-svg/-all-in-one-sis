import { Worker, Job } from 'bullmq'
import { db, users, cravingPredictions } from '@clearpath/db'
import { eq, and } from 'drizzle-orm'
import { predictNextCraving } from '@clearpath/ai-pipeline'
import { pushNotificationsQueue } from '../index.js'

export interface CravingPredictorPayload {
  userId?: string
}

async function runPredictionForUser(userId: string): Promise<void> {
  const [user] = await db.select().from(users).where(eq(users.id, userId)).limit(1)
  if (!user || !user.quitDate || user.subscriptionTier === 'FREE') return

  const prediction = await predictNextCraving(db, userId, user.substanceType)
  if (!prediction) return

  // Store prediction record
  const [savedPrediction] = await db.insert(cravingPredictions).values({
    userId,
    substanceType: user.substanceType,
    predictedAt: prediction.estimatedWindowStart,
    confidence: prediction.confidence,
    triggerFactors: prediction.triggerFactors,
  }).returning()

  if (!savedPrediction) return

  // Schedule push notification 30 min before predicted window
  const msUntilWindow = prediction.estimatedWindowStart.getTime() - Date.now() - 30 * 60 * 1000
  if (msUntilWindow > 0 && user.expoPushToken && user.notificationsEnabled) {
    await pushNotificationsQueue.add(
      'craving-prediction',
      {
        token: user.expoPushToken,
        title: `⚡ Heads up, ${user.displayName.split(' ')[0] ?? 'friend'}`,
        body: "Based on your patterns, you might be hit with a craving in about 30 minutes. You've got this.",
        data: { type: 'CRAVING_PREDICTION', screen: 'quick-log', predictionId: savedPrediction.id },
      },
      { delay: msUntilWindow }
    )
  }
}

const redisConnection = {
  host: process.env['UPSTASH_REDIS_HOST'] ?? 'localhost',
  port: parseInt(process.env['UPSTASH_REDIS_PORT'] ?? '6379'),
  password: process.env['UPSTASH_REDIS_PASSWORD'],
  tls: process.env['NODE_ENV'] === 'production' ? {} : undefined,
}

export const cravingPredictorWorker = new Worker<CravingPredictorPayload>(
  'craving-predictor',
  async (job: Job<CravingPredictorPayload>) => {
    if (job.data.userId) {
      await runPredictionForUser(job.data.userId)
      return
    }

    // Process all premium users
    const premiumUsers = await db.select({ id: users.id })
      .from(users)
      .where(eq(users.subscriptionTier, 'PREMIUM'))

    await Promise.allSettled(premiumUsers.map((u) => runPredictionForUser(u.id)))
    return { processed: premiumUsers.length }
  },
  { connection: redisConnection, concurrency: 3 }
)

cravingPredictorWorker.on('failed', (job, err) => {
  console.error(`Craving predictor job ${job?.id} failed:`, err)
})
