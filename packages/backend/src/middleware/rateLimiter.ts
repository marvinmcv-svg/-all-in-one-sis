import { Request, Response, NextFunction } from 'express'

const aiMessageCounts: Map<string, { count: number; resetAt: Date }> = new Map()

export function aiRateLimit(req: Request, res: Response, next: NextFunction): void {
  if (!req.user) {
    next()
    return
  }

  if (req.user.subscriptionTier !== 'FREE') {
    next()
    return
  }

  const userId = req.user.id
  const now = new Date()
  const entry = aiMessageCounts.get(userId)

  if (!entry || entry.resetAt < now) {
    aiMessageCounts.set(userId, { count: 1, resetAt: new Date(now.setHours(24, 0, 0, 0)) })
    next()
    return
  }

  if (entry.count >= 3) {
    res.status(429).json({
      success: false,
      error: 'Daily AI message limit reached. Upgrade to Premium for unlimited messages.',
      data: null
    })
    return
  }

  entry.count++
  next()
}
