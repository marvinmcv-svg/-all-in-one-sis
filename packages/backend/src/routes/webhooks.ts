import { Router } from 'express'
import { db, users } from '@clearpath/db'
import { eq } from 'drizzle-orm'

export const webhookRouter = Router()

webhookRouter.post('/clerk', async (req, res) => {
  try {
    const { type, data } = req.body as {
      type: string
      data: { id: string; email_addresses: Array<{ email_address: string }>; first_name?: string; image_url?: string }
    }

    if (type === 'user.created') {
      const email = data.email_addresses[0]?.email_address ?? ''
      await db.insert(users).values({
        clerkId: data.id,
        email,
        displayName: data.first_name ?? email.split('@')[0] ?? 'User',
        avatarUrl: data.image_url ?? null,
      }).onConflictDoNothing()
    } else if (type === 'user.deleted') {
      await db.delete(users).where(eq(users.clerkId, data.id))
    }

    res.json({ success: true })
  } catch {
    res.status(500).json({ success: false, error: 'Webhook processing failed' })
  }
})

webhookRouter.post('/revenuecat', async (req, res) => {
  try {
    const { event } = req.body as {
      event: {
        type: string
        app_user_id: string
      }
    }

    const tierMap: Record<string, 'FREE' | 'PREMIUM'> = {
      'INITIAL_PURCHASE': 'PREMIUM',
      'RENEWAL': 'PREMIUM',
      'EXPIRATION': 'FREE',
    }

    const newTier = tierMap[event.type]
    if (newTier) {
      await db.update(users)
        .set({ subscriptionTier: newTier, updatedAt: new Date() })
        .where(eq(users.clerkId, event.app_user_id))
    }

    res.json({ success: true })
  } catch {
    res.status(500).json({ success: false, error: 'Webhook processing failed' })
  }
})
