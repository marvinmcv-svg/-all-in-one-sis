import { Router } from 'express'
import { db, aiMessages, users } from '@clearpath/db'
import { eq, desc, and } from 'drizzle-orm'
import { requireUser } from '../middleware/auth.js'
import { aiRateLimit } from '../middleware/rateLimiter.js'
import { streamCoachResponse } from '@clearpath/ai-pipeline'
import xss from 'xss'

export const aiRouter = Router()
aiRouter.use(requireUser)

const CRISIS_KEYWORDS = ['kill myself', 'not worth living', 'end it', 'hurt myself', 'suicidal', 'want to die']

function detectCrisis(text: string): boolean {
  const lower = text.toLowerCase()
  return CRISIS_KEYWORDS.some((kw) => lower.includes(kw))
}

aiRouter.post('/chat', aiRateLimit, async (req, res) => {
  try {
    const { message, sessionId, messageType = 'COACHING' } = req.body as {
      message: string
      sessionId: string
      messageType?: 'COACHING' | 'CRISIS' | 'CBT' | 'GENERAL'
    }

    const sanitizedMessage = xss(message)
    const isCrisis = detectCrisis(sanitizedMessage)
    const effectiveType = isCrisis ? 'CRISIS' : messageType

    const user = req.user!
    const daysClean = user.quitDate
      ? Math.floor((Date.now() - user.quitDate.getTime()) / (1000 * 60 * 60 * 24))
      : 0

    await db.insert(aiMessages).values({
      userId: user.id,
      role: 'user',
      content: sanitizedMessage,
      sessionId,
      messageType: effectiveType,
    })

    const history = await db.select().from(aiMessages)
      .where(and(eq(aiMessages.userId, user.id), eq(aiMessages.sessionId, sessionId)))
      .orderBy(desc(aiMessages.createdAt))
      .limit(20)

    const messages = history.reverse().map((m) => ({ role: m.role as 'user' | 'assistant', content: m.content }))

    res.setHeader('Content-Type', 'text/event-stream')
    res.setHeader('Cache-Control', 'no-cache')
    res.setHeader('Connection', 'keep-alive')

    if (isCrisis) {
      const crisisPrefix = 'data: ' + JSON.stringify({ type: 'crisis', message: 'If you are in crisis, please contact the 988 Suicide & Crisis Lifeline by calling or texting 988. You are not alone.' }) + '\n\n'
      res.write(crisisPrefix)
    }

    let fullResponse = ''
    const stream = await streamCoachResponse(
      user.id,
      messages,
      effectiveType,
      { substanceType: user.substanceType, daysClean }
    )

    const reader = stream.getReader()
    while (true) {
      const { done, value } = await reader.read()
      if (done) break
      fullResponse += value
      res.write(`data: ${JSON.stringify({ type: 'delta', text: value })}\n\n`)
    }

    await db.insert(aiMessages).values({
      userId: user.id,
      role: 'assistant',
      content: fullResponse,
      sessionId,
      messageType: effectiveType,
    })

    await db.update(users).set({ aiMessagesUsedToday: (user.aiMessagesUsedToday ?? 0) + 1 }).where(eq(users.id, user.id))

    res.write(`data: ${JSON.stringify({ type: 'done' })}\n\n`)
    res.end()
  } catch (err) {
    res.write(`data: ${JSON.stringify({ type: 'error', message: 'AI service unavailable' })}\n\n`)
    res.end()
  }
})

aiRouter.get('/sessions', async (req, res) => {
  try {
    const sessions = await db.select({ sessionId: aiMessages.sessionId })
      .from(aiMessages)
      .where(eq(aiMessages.userId, req.user!.id))

    const unique = [...new Set(sessions.map((s) => s.sessionId))]
    res.json({ success: true, data: unique, error: null })
  } catch {
    res.status(500).json({ success: false, data: null, error: 'Failed to fetch sessions' })
  }
})

aiRouter.get('/sessions/:sessionId', async (req, res) => {
  try {
    const msgs = await db.select().from(aiMessages)
      .where(and(eq(aiMessages.userId, req.user!.id), eq(aiMessages.sessionId, req.params['sessionId']!)))
      .orderBy(aiMessages.createdAt)
    res.json({ success: true, data: msgs, error: null })
  } catch {
    res.status(500).json({ success: false, data: null, error: 'Failed to fetch session' })
  }
})

aiRouter.delete('/sessions/:sessionId', async (req, res) => {
  try {
    const { sql } = await import('drizzle-orm')
    await db.delete(aiMessages)
      .where(and(eq(aiMessages.userId, req.user!.id), eq(aiMessages.sessionId, req.params['sessionId']!)))
    res.json({ success: true, data: { deleted: true }, error: null })
  } catch {
    res.status(500).json({ success: false, data: null, error: 'Failed to delete session' })
  }
})

aiRouter.post('/crisis', async (req, res) => {
  res.json({
    success: true,
    data: {
      message: 'You are not alone. Please reach out to the 988 Suicide & Crisis Lifeline by calling or texting 988.',
      resources: [
        { name: '988 Suicide & Crisis Lifeline', contact: 'Call or text 988' },
        { name: 'Crisis Text Line', contact: 'Text HOME to 741741' },
        { name: 'SAMHSA National Helpline', contact: '1-800-662-4357' },
      ]
    },
    error: null
  })
})

aiRouter.get('/usage', async (req, res) => {
  const user = req.user!
  const limit = user.subscriptionTier === 'FREE' ? 3 : -1
  res.json({
    success: true,
    data: {
      used: user.aiMessagesUsedToday,
      limit,
      unlimited: limit === -1,
    },
    error: null
  })
})
