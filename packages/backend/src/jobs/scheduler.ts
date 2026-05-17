import { cravingPredictorQueue, streakCheckerQueue, cbtReminderQueue, weeklyInsightQueue } from './index.js'
import { badgeEvaluatorWorker } from './workers/badge-evaluator.worker.js'
import { streakCheckerWorker } from './workers/streak-checker.worker.js'
import { cbtReminderWorker } from './workers/cbt-reminder.worker.js'
import { weeklyInsightWorker } from './workers/weekly-insight.worker.js'
import { cravingPredictorWorker } from './workers/craving-predictor.worker.js'
import { pushNotificationsWorker } from './workers/push-notifications.worker.js'

export async function startScheduler(): Promise<void> {
  console.log('Starting ClearPath background job scheduler...')

  // Craving predictor — every 4 hours
  await cravingPredictorQueue.add(
    'run-predictions',
    {},
    { repeat: { pattern: '0 */4 * * *' }, jobId: 'craving-predictor-cron' }
  )

  // Streak checker — daily at midnight UTC
  await streakCheckerQueue.add(
    'check-streaks',
    {},
    { repeat: { pattern: '0 0 * * *' }, jobId: 'streak-checker-cron' }
  )

  // CBT reminder — daily at 20:00 UTC (8 PM)
  await cbtReminderQueue.add(
    'send-cbt-reminders',
    {},
    { repeat: { pattern: '0 20 * * *' }, jobId: 'cbt-reminder-cron' }
  )

  // Weekly insight — every Sunday at 18:00 UTC
  await weeklyInsightQueue.add(
    'generate-insights',
    {},
    { repeat: { pattern: '0 18 * * 0' }, jobId: 'weekly-insight-cron' }
  )

  console.log('Scheduler started. Workers listening:')
  console.log('  ✓ craving-predictor (every 4h)')
  console.log('  ✓ streak-checker (daily midnight)')
  console.log('  ✓ cbt-reminder (daily 8pm UTC)')
  console.log('  ✓ weekly-insight (Sundays 6pm UTC)')
  console.log('  ✓ badge-evaluator (event-driven)')
  console.log('  ✓ push-notifications (event-driven)')
}

// Export workers so server.ts can shut them down gracefully
export const workers = [
  badgeEvaluatorWorker,
  streakCheckerWorker,
  cbtReminderWorker,
  weeklyInsightWorker,
  cravingPredictorWorker,
  pushNotificationsWorker,
]
