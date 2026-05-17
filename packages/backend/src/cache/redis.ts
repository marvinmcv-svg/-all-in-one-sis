import { Redis } from '@upstash/redis'

let _redis: Redis | null = null

export function getRedis(): Redis {
  if (!_redis) {
    _redis = new Redis({
      url: process.env['UPSTASH_REDIS_REST_URL']!,
      token: process.env['UPSTASH_REDIS_REST_TOKEN']!,
    })
  }
  return _redis
}

export async function getCached<T>(key: string): Promise<T | null> {
  try {
    return await getRedis().get<T>(key)
  } catch {
    return null
  }
}

export async function setCached(key: string, value: unknown, ttlSeconds: number): Promise<void> {
  try {
    await getRedis().set(key, JSON.stringify(value), { ex: ttlSeconds })
  } catch {
    // Cache failures are non-fatal
  }
}
