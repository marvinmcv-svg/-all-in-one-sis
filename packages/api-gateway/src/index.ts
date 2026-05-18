import { Hono } from 'hono'
import { cors } from 'hono/cors'
import { logger } from 'hono/logger'
import { clerkMiddleware, getAuth } from '@hono/clerk-auth'
import { Ratelimit } from '@upstash/ratelimit'
import { Redis } from '@upstash/redis/cloudflare'

type Env = {
  CLERK_SECRET_KEY: string
  CLERK_PUBLISHABLE_KEY: string
  UPSTASH_REDIS_REST_URL: string
  UPSTASH_REDIS_REST_TOKEN: string
  BACKEND_URL: string
  CACHE: KVNamespace
}

const app = new Hono<{ Bindings: Env }>()

app.use('*', logger())
app.use('*', cors({
  origin: ['https://clearpath.app', 'http://localhost:3000'],
  allowHeaders: ['Authorization', 'Content-Type'],
  allowMethods: ['GET', 'POST', 'PUT', 'DELETE', 'PATCH'],
}))
app.use('*', clerkMiddleware())

app.use('/api/*', async (c, next) => {
  const redis = new Redis({
    url: c.env.UPSTASH_REDIS_REST_URL,
    token: c.env.UPSTASH_REDIS_REST_TOKEN,
  })
  const limiter = new Ratelimit({
    redis,
    limiter: Ratelimit.slidingWindow(60, '1 m'),
    analytics: true,
  })
  const auth = getAuth(c)
  const identifier = auth?.userId ?? c.req.header('CF-Connecting-IP') ?? 'anon'
  const { success, remaining } = await limiter.limit(identifier)

  c.header('X-RateLimit-Remaining', String(remaining))
  if (!success) return c.json({ success: false, error: 'Rate limit exceeded' }, 429)
  await next()
})

app.use('/api/v1/*', async (c, next) => {
  const auth = getAuth(c)
  if (!auth?.userId) return c.json({ success: false, error: 'Unauthorized' }, 401)
  c.set('userId' as never, auth.userId)
  await next()
})

app.all('/api/v1/*', async (c) => {
  const url = new URL(c.req.url)
  const backendUrl = new URL(c.env.BACKEND_URL)
  url.hostname = backendUrl.hostname
  url.protocol = backendUrl.protocol
  url.port = backendUrl.port

  const headers = new Headers(c.req.raw.headers)
  headers.set('X-Clerk-User-Id', getAuth(c)?.userId ?? '')
  headers.set('X-Request-Id', crypto.randomUUID())

  const response = await fetch(url.toString(), {
    method: c.req.method,
    headers,
    body: ['GET', 'HEAD'].includes(c.req.method) ? undefined : c.req.raw.body,
  })
  return new Response(response.body, {
    status: response.status,
    headers: response.headers,
  })
})

app.get('/health', (c) => c.json({ status: 'ok', ts: new Date().toISOString() }))

export default app
