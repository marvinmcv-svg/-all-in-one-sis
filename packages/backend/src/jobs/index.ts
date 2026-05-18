import { Queue, Worker } from 'bullmq'

const redisConnection = {
  host: process.env['UPSTASH_REDIS_HOST'] ?? 'localhost',
  port: parseInt(process.env['UPSTASH_REDIS_PORT'] ?? '6379'),
  password: process.env['UPSTASH_REDIS_PASSWORD'],
  tls: process.env['NODE_ENV'] === 'production' ? {} : undefined,
}

export const bullmqRedisConnection = redisConnection

export const cravingPredictorQueue = new Queue('craving-predictor', { connection: redisConnection })
export const pushNotificationsQueue = new Queue('push-notifications', { connection: redisConnection })
export const streakCheckerQueue = new Queue('streak-checker', { connection: redisConnection })
export const cbtReminderQueue = new Queue('cbt-reminder', { connection: redisConnection })
export const weeklyInsightQueue = new Queue('weekly-insight', { connection: redisConnection })
export const badgeEvaluatorQueue = new Queue('badge-evaluator', { connection: redisConnection })

export const BADGE_DEFINITIONS = [
  { key: 'day_1',        category: 'TIME_CLEAN' as const,      targetDays: 1,    title: '24 Hours',          description: 'One full day clean',      emoji: '🌱' },
  { key: 'day_3',        category: 'TIME_CLEAN' as const,      targetDays: 3,    title: 'Three Days',         description: 'Three days clean',         emoji: '🌿' },
  { key: 'week_1',       category: 'TIME_CLEAN' as const,      targetDays: 7,    title: 'One Week',           description: 'One full week clean',      emoji: '🌳' },
  { key: 'week_2',       category: 'TIME_CLEAN' as const,      targetDays: 14,   title: 'Two Weeks',          description: 'Two weeks clean',          emoji: '💪' },
  { key: 'month_1',      category: 'TIME_CLEAN' as const,      targetDays: 30,   title: 'One Month',          description: 'One month clean',          emoji: '🏆' },
  { key: 'month_3',      category: 'TIME_CLEAN' as const,      targetDays: 90,   title: 'Three Months',       description: 'Three months clean',       emoji: '💎' },
  { key: 'month_6',      category: 'TIME_CLEAN' as const,      targetDays: 180,  title: 'Six Months',         description: 'Six months clean',         emoji: '🌟' },
  { key: 'year_1',       category: 'TIME_CLEAN' as const,      targetDays: 365,  title: 'One Year',           description: 'One full year clean',      emoji: '👑' },
  { key: 'saved_50',     category: 'MONEY_SAVED' as const,     targetCents: 5000,  title: '$50 Saved',        description: 'Saved $50 since quitting', emoji: '💰' },
  { key: 'saved_100',    category: 'MONEY_SAVED' as const,     targetCents: 10000, title: '$100 Saved',       description: 'Saved $100 since quitting',emoji: '💵' },
  { key: 'cbt_week1',    category: 'CBT_PROGRESS' as const,    weeks: 1,         title: 'CBT Week 1 Done',    description: 'Completed Week 1 of CBT',  emoji: '🧠' },
  { key: 'craving_5',    category: 'CRAVINGS_BEATEN' as const, count: 5,         title: 'Beat 5 Cravings',    description: 'Beat 5 cravings total',    emoji: '⚡' },
  { key: 'craving_25',   category: 'CRAVINGS_BEATEN' as const, count: 25,        title: '25 Cravings Beaten', description: 'Beat 25 cravings total',   emoji: '🛡️' },
  { key: 'streak_7',     category: 'STREAK' as const,          days: 7,          title: '7-Day Streak',       description: '7 consecutive days logged',emoji: '🔥' },
  { key: 'first_post',   category: 'COMMUNITY' as const,       posts: 1,         title: 'First Post',         description: 'Made your first community post', emoji: '💬' },
] as const
