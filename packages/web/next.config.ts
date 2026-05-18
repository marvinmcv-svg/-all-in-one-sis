import type { NextConfig } from 'next'

const BACKEND_URL = process.env['BACKEND_URL'] ?? 'http://localhost:3001'

const nextConfig: NextConfig = {
  transpilePackages: ['@clearpath/shared-types'],
  async rewrites() {
    return [
      {
        source: '/api/v1/:path*',
        destination: `${BACKEND_URL}/api/v1/:path*`,
      },
      {
        source: '/webhooks/:path*',
        destination: `${BACKEND_URL}/webhooks/:path*`,
      },
    ]
  },
}

export default nextConfig
