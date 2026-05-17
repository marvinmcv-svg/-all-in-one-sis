import { Worker, Job } from 'bullmq'
import { sendPushNotification } from '../../push/expo-push.js'
import { db, pushNotificationLogs } from '@clearpath/db'

export interface PushNotificationPayload {
  token: string
  title: string
  body: string
  data?: Record<string, string>
  userId?: string
}

const redisConnection = {
  host: process.env['UPSTASH_REDIS_HOST'] ?? 'localhost',
  port: parseInt(process.env['UPSTASH_REDIS_PORT'] ?? '6379'),
  password: process.env['UPSTASH_REDIS_PASSWORD'],
  tls: process.env['NODE_ENV'] === 'production' ? {} : undefined,
}

export const pushNotificationsWorker = new Worker<PushNotificationPayload>(
  'push-notifications',
  async (job: Job<PushNotificationPayload>) => {
    const { token, title, body, data, userId } = job.data

    await sendPushNotification({ token, title, body, data })

    // Log to DB if we have a userId
    if (userId) {
      await db.insert(pushNotificationLogs).values({
        userId,
        type: data?.['type'] ?? 'UNKNOWN',
        title,
        body,
        data,
      }).catch(() => {}) // non-critical
    }
  },
  { connection: redisConnection, concurrency: 10 }
)

pushNotificationsWorker.on('failed', (job, err) => {
  console.error(`Push notification job ${job?.id} failed:`, err)
})
