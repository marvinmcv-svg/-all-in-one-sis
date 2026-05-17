import { Request, Response, NextFunction } from 'express'
import { db, users } from '@clearpath/db'
import { eq } from 'drizzle-orm'

declare global {
  namespace Express {
    interface Request {
      user?: typeof users.$inferSelect
    }
  }
}

export async function requireUser(req: Request, res: Response, next: NextFunction): Promise<void> {
  const clerkId = req.headers['x-clerk-user-id'] as string | undefined
  if (!clerkId) {
    res.status(401).json({ success: false, error: 'Unauthorized', data: null })
    return
  }

  const [user] = await db.select().from(users).where(eq(users.clerkId, clerkId)).limit(1)
  if (!user) {
    res.status(404).json({ success: false, error: 'User not found', data: null })
    return
  }

  req.user = user
  next()
}

export function requirePremium(req: Request, res: Response, next: NextFunction): void {
  if (!req.user || req.user.subscriptionTier === 'FREE') {
    res.status(403).json({ success: false, error: 'Premium subscription required', data: null })
    return
  }
  next()
}
