import { Router } from 'express'
import { db, users, nicotineProfiles, cannabisProfiles } from '@clearpath/db'
import { eq } from 'drizzle-orm'
import { requireUser } from '../middleware/auth.js'
import { OnboardingFormSchema } from '@clearpath/shared-types'
import xss from 'xss'

export const userRouter = Router()

userRouter.post('/sync', async (req, res) => {
  try {
    const { clerkId, email, displayName, avatarUrl } = req.body as {
      clerkId: string
      email: string
      displayName: string
      avatarUrl?: string
    }

    const existing = await db.select().from(users).where(eq(users.clerkId, clerkId)).limit(1)
    if (existing.length > 0) {
      res.json({ success: true, data: existing[0], error: null })
      return
    }

    const adjectives = ['Brave', 'Calm', 'Clear', 'Bold', 'Free', 'Strong', 'Bright', 'Swift']
    const nouns = ['Hawk', 'River', 'Mountain', 'Falcon', 'Storm', 'Oak', 'Star', 'Path']
    const alias = `${adjectives[Math.floor(Math.random() * adjectives.length)]}_${nouns[Math.floor(Math.random() * nouns.length)]}_${Math.floor(Math.random() * 1000)}`

    const [newUser] = await db.insert(users).values({
      clerkId,
      email: xss(email),
      displayName: xss(displayName),
      avatarUrl: avatarUrl ?? null,
      anonymousAlias: alias,
    }).returning()

    res.status(201).json({ success: true, data: newUser, error: null })
  } catch (err) {
    res.status(500).json({ success: false, data: null, error: 'Failed to sync user' })
  }
})

userRouter.get('/me', requireUser, async (req, res) => {
  res.json({ success: true, data: req.user, error: null })
})

userRouter.put('/me', requireUser, async (req, res) => {
  try {
    const { displayName, timezone, notificationsEnabled } = req.body as {
      displayName?: string
      timezone?: string
      notificationsEnabled?: boolean
    }

    const updates: Partial<typeof users.$inferInsert> = { updatedAt: new Date() }
    if (displayName !== undefined) updates.displayName = xss(displayName)
    if (timezone !== undefined) updates.timezone = timezone
    if (notificationsEnabled !== undefined) updates.notificationsEnabled = notificationsEnabled

    const [updated] = await db.update(users).set(updates).where(eq(users.id, req.user!.id)).returning()
    res.json({ success: true, data: updated, error: null })
  } catch {
    res.status(500).json({ success: false, data: null, error: 'Failed to update user' })
  }
})

userRouter.post('/onboarding', requireUser, async (req, res) => {
  try {
    const form = OnboardingFormSchema.parse(req.body)
    const userId = req.user!.id

    await db.update(users).set({
      substanceType: form.substanceType,
      quitGoal: form.quitGoal,
      quitDate: form.quitDate ? new Date(form.quitDate) : null,
      timezone: form.timezone,
      notificationsEnabled: form.notificationsEnabled,
      onboardingCompleted: true,
      updatedAt: new Date(),
    }).where(eq(users.id, userId))

    if (form.nicotineProfile && (form.substanceType === 'NICOTINE' || form.substanceType === 'BOTH')) {
      await db.insert(nicotineProfiles).values({ userId, ...form.nicotineProfile })
    }

    if (form.cannabisProfile && (form.substanceType === 'CANNABIS' || form.substanceType === 'BOTH')) {
      await db.insert(cannabisProfiles).values({ userId, ...form.cannabisProfile })
    }

    const [updated] = await db.select().from(users).where(eq(users.id, userId)).limit(1)
    res.json({ success: true, data: updated, error: null })
  } catch (err) {
    if (err instanceof Error) {
      res.status(400).json({ success: false, data: null, error: err.message })
    } else {
      res.status(500).json({ success: false, data: null, error: 'Onboarding failed' })
    }
  }
})

userRouter.put('/quit-date', requireUser, async (req, res) => {
  try {
    const { quitDate } = req.body as { quitDate: string }
    const [updated] = await db.update(users).set({
      quitDate: new Date(quitDate),
      updatedAt: new Date(),
    }).where(eq(users.id, req.user!.id)).returning()
    res.json({ success: true, data: updated, error: null })
  } catch {
    res.status(500).json({ success: false, data: null, error: 'Failed to update quit date' })
  }
})

userRouter.put('/push-token', requireUser, async (req, res) => {
  try {
    const { token } = req.body as { token: string }
    const [updated] = await db.update(users).set({
      expoPushToken: token,
      updatedAt: new Date(),
    }).where(eq(users.id, req.user!.id)).returning()
    res.json({ success: true, data: updated, error: null })
  } catch {
    res.status(500).json({ success: false, data: null, error: 'Failed to update push token' })
  }
})

userRouter.delete('/me', requireUser, async (req, res) => {
  try {
    await db.delete(users).where(eq(users.id, req.user!.id))
    res.json({ success: true, data: { deleted: true }, error: null })
  } catch {
    res.status(500).json({ success: false, data: null, error: 'Failed to delete account' })
  }
})
