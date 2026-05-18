import { Router } from 'express'
import { createHmac, timingSafeEqual } from 'crypto'
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
      const adjectives = ['Brave', 'Calm', 'Bold', 'Kind', 'Wise', 'Clear', 'Free', 'Strong', 'Bright', 'Steady']
      const animals = ['Falcon', 'Otter', 'Fox', 'Wolf', 'Bear', 'Hawk', 'Deer', 'Lynx', 'Eagle', 'Crane']
      const adj = adjectives[Math.floor(Math.random() * adjectives.length)]!
      const animal = animals[Math.floor(Math.random() * animals.length)]!
      const suffix = Math.floor(Math.random() * 900) + 100
      const anonymousAlias = `${adj}${animal}${suffix}`

      await db.insert(users).values({
        clerkId: data.id,
        email,
        displayName: data.first_name ?? email.split('@')[0] ?? 'User',
        avatarUrl: data.image_url ?? null,
        anonymousAlias,
      }).onConflictDoNothing()
    } else if (type === 'user.deleted') {
      await db.delete(users).where(eq(users.clerkId, data.id))
    }

    res.json({ success: true })
  } catch {
    res.status(500).json({ success: false, error: 'Webhook processing failed' })
  }
})

function verifyRevenueCatSignature(payload: string, signature: string, secret: string): boolean {
  try {
    const expected = createHmac('sha256', secret).update(payload).digest('hex')
    return timingSafeEqual(Buffer.from(signature), Buffer.from(expected))
  } catch {
    return false
  }
}

webhookRouter.post('/revenuecat', async (req, res) => {
  try {
    const secret = process.env['REVENUECAT_WEBHOOK_SECRET']
    const signature = req.headers['x-revenuecat-signature'] as string | undefined

    if (secret && signature) {
      const rawBody = JSON.stringify(req.body)
      if (!verifyRevenueCatSignature(rawBody, signature, secret)) {
        res.status(401).json({ success: false, error: 'Invalid signature' })
        return
      }
    }

    const { event } = req.body as {
      event: {
        type: string
        app_user_id: string
        period_type?: string
      }
    }

    const tierMap: Record<string, 'FREE' | 'PREMIUM'> = {
      INITIAL_PURCHASE: 'PREMIUM',
      RENEWAL: 'PREMIUM',
      PRODUCT_CHANGE: 'PREMIUM',
      EXPIRATION: 'FREE',
      CANCELLATION: 'FREE',
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
