import { Router } from 'express'
import { db, journalEntries } from '@clearpath/db'
import { eq, desc, and, gte, lte } from 'drizzle-orm'
import { requireUser } from '../middleware/auth.js'
import xss from 'xss'

export const journalRouter = Router()
journalRouter.use(requireUser)

journalRouter.post('/', async (req, res) => {
  try {
    const { title, content, mood, substanceType, audioUrl, transcription } = req.body as {
      title?: string
      content: string
      mood: number
      substanceType?: 'NICOTINE' | 'CANNABIS' | 'BOTH'
      audioUrl?: string
      transcription?: string
    }

    const [entry] = await db.insert(journalEntries).values({
      userId: req.user!.id,
      title: title ? xss(title) : null,
      content: xss(content),
      mood,
      substanceType: substanceType ?? null,
      audioUrl: audioUrl ?? null,
      transcription: transcription ? xss(transcription) : null,
    }).returning()

    res.status(201).json({ success: true, data: entry, error: null })
  } catch {
    res.status(500).json({ success: false, data: null, error: 'Failed to create journal entry' })
  }
})

journalRouter.get('/', async (req, res) => {
  try {
    const { page = '1', limit = '20', dateFrom, dateTo } = req.query as Record<string, string>
    const pageNum = parseInt(page)
    const limitNum = Math.min(parseInt(limit), 50)
    const offset = (pageNum - 1) * limitNum

    const conditions = [eq(journalEntries.userId, req.user!.id)]
    if (dateFrom) conditions.push(gte(journalEntries.createdAt, new Date(dateFrom)))
    if (dateTo) conditions.push(lte(journalEntries.createdAt, new Date(dateTo)))

    const entries = await db.select().from(journalEntries)
      .where(and(...conditions))
      .orderBy(desc(journalEntries.createdAt))
      .limit(limitNum)
      .offset(offset)

    res.json({ success: true, data: entries, pagination: { page: pageNum, limit: limitNum, total: entries.length, hasMore: entries.length === limitNum } })
  } catch {
    res.status(500).json({ success: false, data: null, error: 'Failed to fetch journal' })
  }
})

journalRouter.get('/:id', async (req, res) => {
  try {
    const [entry] = await db.select().from(journalEntries)
      .where(and(eq(journalEntries.id, req.params['id']!), eq(journalEntries.userId, req.user!.id)))
      .limit(1)
    if (!entry) { res.status(404).json({ success: false, data: null, error: 'Not found' }); return }
    res.json({ success: true, data: entry, error: null })
  } catch {
    res.status(500).json({ success: false, data: null, error: 'Failed to fetch entry' })
  }
})

journalRouter.put('/:id', async (req, res) => {
  try {
    const { title, content, mood } = req.body as { title?: string; content?: string; mood?: number }
    const updates: Partial<typeof journalEntries.$inferInsert> = { updatedAt: new Date() }
    if (title !== undefined) updates.title = xss(title)
    if (content !== undefined) updates.content = xss(content)
    if (mood !== undefined) updates.mood = mood

    const [updated] = await db.update(journalEntries).set(updates)
      .where(and(eq(journalEntries.id, req.params['id']!), eq(journalEntries.userId, req.user!.id)))
      .returning()
    res.json({ success: true, data: updated, error: null })
  } catch {
    res.status(500).json({ success: false, data: null, error: 'Failed to update entry' })
  }
})

journalRouter.delete('/:id', async (req, res) => {
  try {
    await db.delete(journalEntries)
      .where(and(eq(journalEntries.id, req.params['id']!), eq(journalEntries.userId, req.user!.id)))
    res.json({ success: true, data: { deleted: true }, error: null })
  } catch {
    res.status(500).json({ success: false, data: null, error: 'Failed to delete entry' })
  }
})

journalRouter.post('/search', async (req, res) => {
  res.json({ success: true, data: [], error: null })
})
