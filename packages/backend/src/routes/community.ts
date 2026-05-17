import { Router } from 'express'
import { db, communityPosts, communityComments, users } from '@clearpath/db'
import { eq, desc, and } from 'drizzle-orm'
import { requireUser } from '../middleware/auth.js'
import xss from 'xss'

export const communityRouter = Router()
communityRouter.use(requireUser)

communityRouter.get('/posts', async (req, res) => {
  try {
    const { page = '1', limit = '20' } = req.query as Record<string, string>
    const pageNum = parseInt(page)
    const limitNum = Math.min(parseInt(limit), 50)
    const offset = (pageNum - 1) * limitNum

    const posts = await db.select({
      id: communityPosts.id,
      anonymousAlias: communityPosts.anonymousAlias,
      title: communityPosts.title,
      content: communityPosts.content,
      substanceTags: communityPosts.substanceTags,
      likes: communityPosts.likes,
      commentCount: communityPosts.commentCount,
      isPinned: communityPosts.isPinned,
      createdAt: communityPosts.createdAt,
      updatedAt: communityPosts.updatedAt,
    })
      .from(communityPosts)
      .orderBy(desc(communityPosts.createdAt))
      .limit(limitNum)
      .offset(offset)

    res.json({ success: true, data: posts, pagination: { page: pageNum, limit: limitNum, total: posts.length, hasMore: posts.length === limitNum } })
  } catch {
    res.status(500).json({ success: false, data: null, error: 'Failed to fetch posts' })
  }
})

communityRouter.post('/posts', async (req, res) => {
  try {
    if (req.user!.subscriptionTier === 'FREE') {
      res.status(403).json({ success: false, data: null, error: 'Premium required to post' })
      return
    }

    const { title, content, substanceTags } = req.body as {
      title: string
      content: string
      substanceTags: string[]
    }

    const [post] = await db.insert(communityPosts).values({
      authorId: req.user!.id,
      anonymousAlias: req.user!.anonymousAlias ?? 'Anonymous',
      title: xss(title),
      content: xss(content),
      substanceTags: substanceTags,
    }).returning({
      id: communityPosts.id,
      anonymousAlias: communityPosts.anonymousAlias,
      title: communityPosts.title,
      content: communityPosts.content,
      substanceTags: communityPosts.substanceTags,
      likes: communityPosts.likes,
      commentCount: communityPosts.commentCount,
      isPinned: communityPosts.isPinned,
      createdAt: communityPosts.createdAt,
      updatedAt: communityPosts.updatedAt,
    })

    res.status(201).json({ success: true, data: post, error: null })
  } catch {
    res.status(500).json({ success: false, data: null, error: 'Failed to create post' })
  }
})

communityRouter.get('/posts/:id', async (req, res) => {
  try {
    const [post] = await db.select({
      id: communityPosts.id,
      anonymousAlias: communityPosts.anonymousAlias,
      title: communityPosts.title,
      content: communityPosts.content,
      substanceTags: communityPosts.substanceTags,
      likes: communityPosts.likes,
      commentCount: communityPosts.commentCount,
      isPinned: communityPosts.isPinned,
      createdAt: communityPosts.createdAt,
      updatedAt: communityPosts.updatedAt,
    })
      .from(communityPosts)
      .where(eq(communityPosts.id, req.params['id']!))
      .limit(1)

    if (!post) { res.status(404).json({ success: false, data: null, error: 'Not found' }); return }
    res.json({ success: true, data: post, error: null })
  } catch {
    res.status(500).json({ success: false, data: null, error: 'Failed to fetch post' })
  }
})

communityRouter.post('/posts/:id/like', async (req, res) => {
  try {
    const [post] = await db.select().from(communityPosts).where(eq(communityPosts.id, req.params['id']!)).limit(1)
    if (!post) { res.status(404).json({ success: false, data: null, error: 'Not found' }); return }
    await db.update(communityPosts).set({ likes: post.likes + 1 }).where(eq(communityPosts.id, post.id))
    res.json({ success: true, data: { likes: post.likes + 1 }, error: null })
  } catch {
    res.status(500).json({ success: false, data: null, error: 'Failed to like post' })
  }
})

communityRouter.get('/posts/:id/comments', async (req, res) => {
  try {
    const comments = await db.select({
      id: communityComments.id,
      anonymousAlias: communityComments.anonymousAlias,
      content: communityComments.content,
      likes: communityComments.likes,
      createdAt: communityComments.createdAt,
    })
      .from(communityComments)
      .where(eq(communityComments.postId, req.params['id']!))
      .orderBy(communityComments.createdAt)

    res.json({ success: true, data: comments, error: null })
  } catch {
    res.status(500).json({ success: false, data: null, error: 'Failed to fetch comments' })
  }
})

communityRouter.post('/posts/:id/comments', async (req, res) => {
  try {
    const { content } = req.body as { content: string }
    const [comment] = await db.insert(communityComments).values({
      postId: req.params['id']!,
      authorId: req.user!.id,
      anonymousAlias: req.user!.anonymousAlias ?? 'Anonymous',
      content: xss(content),
    }).returning({
      id: communityComments.id,
      anonymousAlias: communityComments.anonymousAlias,
      content: communityComments.content,
      likes: communityComments.likes,
      createdAt: communityComments.createdAt,
    })

    await db.update(communityPosts)
      .set({ commentCount: db.select().from(communityComments).where(eq(communityComments.postId, req.params['id']!)).then as never })
      .where(eq(communityPosts.id, req.params['id']!))

    res.status(201).json({ success: true, data: comment, error: null })
  } catch {
    res.status(500).json({ success: false, data: null, error: 'Failed to add comment' })
  }
})

communityRouter.delete('/comments/:id', async (req, res) => {
  try {
    await db.delete(communityComments)
      .where(and(eq(communityComments.id, req.params['id']!), eq(communityComments.authorId, req.user!.id)))
    res.json({ success: true, data: { deleted: true }, error: null })
  } catch {
    res.status(500).json({ success: false, data: null, error: 'Failed to delete comment' })
  }
})

communityRouter.post('/posts/:id/report', async (req, res) => {
  res.json({ success: true, data: { reported: true }, error: null })
})
