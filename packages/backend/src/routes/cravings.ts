import { Router } from 'express'
import { db, cravingLogs, usageLogs } from '@clearpath/db'
import { eq, desc, gte, lte, and, sql } from 'drizzle-orm'
import { requireUser } from '../middleware/auth.js'
import xss from 'xss'
import { badgeEvaluatorQueue } from '../jobs/index.js'

export const cravingRouter = Router()

cravingRouter.use(requireUser)

cravingRouter.post('/', async (req, res) => {
  try {
    const { substanceType, intensity, triggered, triggerTags, mood, location, copingUsed, notes, loggedAt } = req.body as {
      substanceType: 'NICOTINE' | 'CANNABIS' | 'BOTH'
      intensity: 'LOW' | 'MEDIUM' | 'HIGH' | 'OVERWHELMING'
      triggered: boolean
      triggerTags: string[]
      mood: number
      location?: string
      copingUsed?: string
      notes?: string
      loggedAt?: string
    }

    const [log] = await db.insert(cravingLogs).values({
      userId: req.user!.id,
      substanceType,
      intensity,
      triggered,
      triggerTags: triggerTags.map((t) => xss(t)),
      mood,
      location: location ? xss(location) : null,
      copingUsed: copingUsed ? xss(copingUsed) : null,
      notes: notes ? xss(notes) : null,
      loggedAt: loggedAt ? new Date(loggedAt) : new Date(),
    }).returning()

    // Evaluate badges in the background
    badgeEvaluatorQueue.add('evaluate', { userId: req.user!.id }).catch(() => {})

    res.status(201).json({ success: true, data: log, error: null })
  } catch {
    res.status(500).json({ success: false, data: null, error: 'Failed to log craving' })
  }
})

cravingRouter.get('/', async (req, res) => {
  try {
    const { page = '1', limit = '20', substanceType, dateFrom, dateTo } = req.query as Record<string, string>
    const pageNum = parseInt(page)
    const limitNum = Math.min(parseInt(limit), 100)
    const offset = (pageNum - 1) * limitNum

    const conditions = [eq(cravingLogs.userId, req.user!.id)]
    if (substanceType) conditions.push(eq(cravingLogs.substanceType, substanceType as 'NICOTINE' | 'CANNABIS' | 'BOTH'))
    if (dateFrom) conditions.push(gte(cravingLogs.loggedAt, new Date(dateFrom)))
    if (dateTo) conditions.push(lte(cravingLogs.loggedAt, new Date(dateTo)))

    const logs = await db.select().from(cravingLogs)
      .where(and(...conditions))
      .orderBy(desc(cravingLogs.loggedAt))
      .limit(limitNum)
      .offset(offset)

    res.json({ success: true, data: logs, pagination: { page: pageNum, limit: limitNum, total: logs.length, hasMore: logs.length === limitNum } })
  } catch {
    res.status(500).json({ success: false, data: null, error: 'Failed to fetch cravings' })
  }
})

cravingRouter.get('/streak', async (req, res) => {
  try {
    const user = req.user!
    const daysClean = user.quitDate
      ? Math.floor((Date.now() - user.quitDate.getTime()) / (1000 * 60 * 60 * 24))
      : 0

    res.json({
      success: true,
      data: {
        currentStreakDays: daysClean,
        longestStreakDays: user.longestStreakDays,
      },
      error: null
    })
  } catch {
    res.status(500).json({ success: false, data: null, error: 'Failed to fetch streak' })
  }
})

cravingRouter.get('/triggers/summary', async (req, res) => {
  try {
    const thirtyDaysAgo = new Date(Date.now() - 30 * 24 * 60 * 60 * 1000)
    const logs = await db.select().from(cravingLogs)
      .where(and(eq(cravingLogs.userId, req.user!.id), gte(cravingLogs.loggedAt, thirtyDaysAgo)))

    const tagCounts: Record<string, number> = {}
    for (const log of logs) {
      for (const tag of (log.triggerTags as string[])) {
        tagCounts[tag] = (tagCounts[tag] ?? 0) + 1
      }
    }

    const summary = Object.entries(tagCounts)
      .sort((a, b) => b[1] - a[1])
      .slice(0, 10)
      .map(([tag, count]) => ({ tag, count }))

    res.json({ success: true, data: summary, error: null })
  } catch {
    res.status(500).json({ success: false, data: null, error: 'Failed to fetch triggers' })
  }
})

cravingRouter.get('/:id', async (req, res) => {
  try {
    const [log] = await db.select().from(cravingLogs)
      .where(and(eq(cravingLogs.id, req.params['id']!), eq(cravingLogs.userId, req.user!.id)))
      .limit(1)
    if (!log) { res.status(404).json({ success: false, data: null, error: 'Not found' }); return }
    res.json({ success: true, data: log, error: null })
  } catch {
    res.status(500).json({ success: false, data: null, error: 'Failed to fetch craving' })
  }
})

cravingRouter.put('/:id', async (req, res) => {
  try {
    const { copingUsed, notes } = req.body as { copingUsed?: string; notes?: string }
    const [updated] = await db.update(cravingLogs)
      .set({ copingUsed: copingUsed ? xss(copingUsed) : undefined, notes: notes ? xss(notes) : undefined })
      .where(and(eq(cravingLogs.id, req.params['id']!), eq(cravingLogs.userId, req.user!.id)))
      .returning()
    res.json({ success: true, data: updated, error: null })
  } catch {
    res.status(500).json({ success: false, data: null, error: 'Failed to update craving' })
  }
})

cravingRouter.delete('/:id', async (req, res) => {
  try {
    await db.delete(cravingLogs)
      .where(and(eq(cravingLogs.id, req.params['id']!), eq(cravingLogs.userId, req.user!.id)))
    res.json({ success: true, data: { deleted: true }, error: null })
  } catch {
    res.status(500).json({ success: false, data: null, error: 'Failed to delete craving' })
  }
})

// Usage logs
const usageRouter = Router()
usageRouter.use(requireUser)

usageRouter.post('/', async (req, res) => {
  try {
    const { substanceType, amount, mood, triggerTags, notes, loggedAt } = req.body as {
      substanceType: 'NICOTINE' | 'CANNABIS' | 'BOTH'
      amount: number
      mood: number
      triggerTags: string[]
      notes?: string
      loggedAt?: string
    }

    const [log] = await db.insert(usageLogs).values({
      userId: req.user!.id,
      substanceType,
      amount,
      mood,
      triggerTags: triggerTags.map((t) => xss(t)),
      notes: notes ? xss(notes) : null,
      loggedAt: loggedAt ? new Date(loggedAt) : new Date(),
    }).returning()

    res.status(201).json({ success: true, data: log, error: null })
  } catch {
    res.status(500).json({ success: false, data: null, error: 'Failed to log usage' })
  }
})

usageRouter.get('/', async (req, res) => {
  try {
    const logs = await db.select().from(usageLogs)
      .where(eq(usageLogs.userId, req.user!.id))
      .orderBy(desc(usageLogs.loggedAt))
      .limit(50)
    res.json({ success: true, data: logs, error: null })
  } catch {
    res.status(500).json({ success: false, data: null, error: 'Failed to fetch usage logs' })
  }
})

export { usageRouter }
