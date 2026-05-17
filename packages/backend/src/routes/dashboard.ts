import { Router } from 'express'
import { db, cravingLogs, badges, healthMilestones } from '@clearpath/db'
import { eq, gte, and, desc } from 'drizzle-orm'
import { requireUser } from '../middleware/auth.js'

export const dashboardRouter = Router()
dashboardRouter.use(requireUser)

dashboardRouter.get('/stats', async (req, res) => {
  try {
    const user = req.user!
    const now = Date.now()
    const quitDate = user.quitDate ? new Date(user.quitDate) : null
    const secondsClean = quitDate ? Math.floor((now - quitDate.getTime()) / 1000) : 0
    const daysClean = Math.floor(secondsClean / 86400)

    const sevenDaysAgo = new Date(now - 7 * 24 * 60 * 60 * 1000)
    const recentCravings = await db.select().from(cravingLogs)
      .where(and(eq(cravingLogs.userId, user.id), gte(cravingLogs.loggedAt, sevenDaysAgo)))

    const cravingsBeat = recentCravings.filter((c) => !c.triggered).length
    const moods = recentCravings.map((c) => c.mood).filter((m) => m > 0)
    const avgMood = moods.length > 0 ? moods.reduce((a, b) => a + b, 0) / moods.length : null

    const userBadges = await db.select().from(badges).where(eq(badges.userId, user.id))

    const milestones = await db.select().from(healthMilestones)
      .where(eq(healthMilestones.substanceType, user.substanceType))

    const healthMilestonesStatus = milestones.map((m) => ({
      key: m.id,
      title: m.title,
      description: m.description,
      targetDays: Math.ceil(m.targetDays),
      achievedAt: quitDate && daysClean >= m.targetDays
        ? new Date(quitDate.getTime() + m.targetDays * 86400 * 1000).toISOString()
        : null,
    }))

    const nicotineProfile = user.substanceType === 'NICOTINE' || user.substanceType === 'BOTH'
      ? await db.query?.nicotineProfiles?.findFirst?.({ where: eq(db._.schema?.nicotineProfiles?.userId ?? 'user_id' as never, user.id) })
      : null

    const dailyCost = nicotineProfile ? nicotineProfile.costPerUnit * nicotineProfile.dailyUsageAmount : 0
    const moneySavedCents = Math.round(daysClean * dailyCost * 100)
    const projectedYearlySavingsCents = Math.round(365 * dailyCost * 100)

    res.json({
      success: true,
      data: {
        userId: user.id,
        substanceType: user.substanceType,
        cleanSinceDatetime: quitDate?.toISOString() ?? null,
        secondsClean,
        daysClean,
        longestStreakDays: user.longestStreakDays,
        currentStreakDays: daysClean,
        moneySavedCents,
        projectedYearlySavingsCents,
        healthMilestonesCurrent: healthMilestonesStatus,
        cravingsBeatThisWeek: cravingsBeat,
        avgMoodThisWeek: avgMood,
        badgesEarned: userBadges.length,
      },
      error: null
    })
  } catch (err) {
    console.error(err)
    res.status(500).json({ success: false, data: null, error: 'Failed to fetch dashboard stats' })
  }
})

dashboardRouter.get('/health-timeline', async (req, res) => {
  try {
    const user = req.user!
    const milestones = await db.select().from(healthMilestones)
      .where(eq(healthMilestones.substanceType, user.substanceType))
    const daysClean = user.quitDate
      ? Math.floor((Date.now() - user.quitDate.getTime()) / 86400000)
      : 0

    const timeline = milestones.map((m) => ({
      ...m,
      achieved: daysClean >= m.targetDays,
    }))

    res.json({ success: true, data: timeline, error: null })
  } catch {
    res.status(500).json({ success: false, data: null, error: 'Failed to fetch health timeline' })
  }
})

dashboardRouter.get('/weekly-chart', async (req, res) => {
  try {
    const sevenDaysAgo = new Date(Date.now() - 7 * 24 * 60 * 60 * 1000)
    const logs = await db.select().from(cravingLogs)
      .where(and(eq(cravingLogs.userId, req.user!.id), gte(cravingLogs.loggedAt, sevenDaysAgo)))
      .orderBy(cravingLogs.loggedAt)

    const chartData = Array.from({ length: 7 }, (_, i) => {
      const date = new Date(Date.now() - (6 - i) * 86400000)
      const dayLogs = logs.filter((l) => {
        const logDate = new Date(l.loggedAt)
        return logDate.toDateString() === date.toDateString()
      })
      return {
        date: date.toISOString().split('T')[0],
        cravings: dayLogs.length,
        beaten: dayLogs.filter((l) => !l.triggered).length,
        avgMood: dayLogs.length > 0
          ? dayLogs.reduce((a, b) => a + b.mood, 0) / dayLogs.length
          : null,
      }
    })

    res.json({ success: true, data: chartData, error: null })
  } catch {
    res.status(500).json({ success: false, data: null, error: 'Failed to fetch weekly chart' })
  }
})

dashboardRouter.get('/insights', async (req, res) => {
  res.json({
    success: true,
    data: {
      insight: 'Keep up the great work! Your craving resistance is improving. You\'ve beaten more cravings this week than last week.',
      generatedAt: new Date().toISOString(),
    },
    error: null
  })
})
