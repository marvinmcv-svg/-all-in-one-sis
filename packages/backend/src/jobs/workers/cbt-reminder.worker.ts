import { Worker, Job } from 'bullmq'
import { db, users, cbtModules } from '@clearpath/db'
import { eq, and } from 'drizzle-orm'
import { pushNotificationsQueue } from '../index.js'

export interface CbtReminderPayload {
  userId?: string
}

const CBT_LESSON_TITLES: Record<string, string> = {
  '1-1': 'The Science of Your Addiction',
  '1-2': 'Craving Anatomy — 90 Seconds',
  '1-3': 'Trigger Mapping',
  '1-4': 'Urge Surfing',
  '1-5': 'Values Clarification',
  '1-6': 'Emergency Toolkit',
  '1-7': 'Week 1 Reflection',
  '2-1': 'Introduction to Automatic Thoughts',
  '2-2': 'Thought Record Exercise',
  '2-3': 'Cognitive Distortions',
  '2-4': 'Challenging "I Deserve This"',
  '2-5': 'Behavioral Activation',
  '2-6': 'Social Triggers Deep Dive',
  '2-7': 'Week 2 Reflection',
}

async function sendCbtReminderForUser(userId: string): Promise<void> {
  const [user] = await db.select().from(users).where(eq(users.id, userId)).limit(1)
  if (!user || !user.onboardingCompleted || !user.expoPushToken || !user.notificationsEnabled) return

  // Find the next incomplete lesson
  const completedModules = await db.select().from(cbtModules)
    .where(and(eq(cbtModules.userId, userId)))

  const completedCount = completedModules.filter((m) => m.completedAt !== null).length
  const nextWeek = Math.floor(completedCount / 7) + 1
  const nextLesson = (completedCount % 7) + 1

  if (nextWeek > 6) return // Program completed

  // Check if today's lesson is already done
  const todayLesson = completedModules.find(
    (m) => m.weekNumber === nextWeek && m.lessonNumber === nextLesson && m.completedAt !== null
  )
  if (todayLesson) return

  const lessonTitle = CBT_LESSON_TITLES[`${nextWeek}-${nextLesson}`] ?? `Week ${nextWeek}, Day ${nextLesson}`

  await pushNotificationsQueue.add('cbt-reminder', {
    token: user.expoPushToken,
    title: '🧠 Your daily lesson is waiting',
    body: `Week ${nextWeek}, Day ${nextLesson}: ${lessonTitle}. Takes 5 minutes.`,
    data: { type: 'CBT_REMINDER', screen: 'cbt' },
  })
}

const redisConnection = {
  host: process.env['UPSTASH_REDIS_HOST'] ?? 'localhost',
  port: parseInt(process.env['UPSTASH_REDIS_PORT'] ?? '6379'),
  password: process.env['UPSTASH_REDIS_PASSWORD'],
  tls: process.env['NODE_ENV'] === 'production' ? {} : undefined,
}

export const cbtReminderWorker = new Worker<CbtReminderPayload>(
  'cbt-reminder',
  async (job: Job<CbtReminderPayload>) => {
    if (job.data.userId) {
      await sendCbtReminderForUser(job.data.userId)
      return
    }

    const premiumUsers = await db.select({ id: users.id })
      .from(users)
      .where(eq(users.notificationsEnabled, true))

    await Promise.allSettled(premiumUsers.map((u) => sendCbtReminderForUser(u.id)))
    return { processed: premiumUsers.length }
  },
  { connection: redisConnection, concurrency: 2 }
)

cbtReminderWorker.on('failed', (job, err) => {
  console.error(`CBT reminder job ${job?.id} failed:`, err)
})
