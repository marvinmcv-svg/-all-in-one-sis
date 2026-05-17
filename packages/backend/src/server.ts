import * as Sentry from '@sentry/node'
import express from 'express'
import cors from 'cors'
import helmet from 'helmet'
import { startScheduler, workers } from './jobs/scheduler.js'
import { userRouter } from './routes/users.js'
import { cravingRouter } from './routes/cravings.js'
import { journalRouter } from './routes/journal.js'
import { cbtRouter } from './routes/cbt.js'
import { aiRouter } from './routes/ai.js'
import { communityRouter } from './routes/community.js'
import { dashboardRouter } from './routes/dashboard.js'
import { webhookRouter } from './routes/webhooks.js'
import { errorHandler } from './middleware/error.js'
import { requestLogger } from './middleware/logger.js'

Sentry.init({
  dsn: process.env['SENTRY_DSN'],
  environment: process.env['NODE_ENV'] ?? 'development',
  tracesSampleRate: 0.1,
  integrations: [Sentry.expressIntegration()],
})

const app = express()

app.use(Sentry.requestHandler())
app.use(Sentry.tracingHandler())
app.use(helmet())
app.use(cors({ origin: process.env['API_GATEWAY_URL'] }))
app.use(express.json({ limit: '10mb' }))
app.use(requestLogger)

app.use('/api/v1/users', userRouter)
app.use('/api/v1/cravings', cravingRouter)
app.use('/api/v1/journal', journalRouter)
app.use('/api/v1/cbt', cbtRouter)
app.use('/api/v1/ai', aiRouter)
app.use('/api/v1/community', communityRouter)
app.use('/api/v1/dashboard', dashboardRouter)
app.use('/webhooks', webhookRouter)
app.get('/health', (_, res) => res.json({ status: 'ok' }))

app.use(Sentry.errorHandler())
app.use(errorHandler)

const PORT = process.env['PORT'] ?? 3001
app.listen(PORT, () => console.log(`Backend running on :${PORT}`))

// Start background job workers and cron scheduler
if (process.env['NODE_ENV'] !== 'test') {
  startScheduler().catch(console.error)
}

// Graceful shutdown
process.on('SIGTERM', async () => {
  console.log('Shutting down gracefully...')
  await Promise.all(workers.map((w) => w.close()))
  process.exit(0)
})
