import type { NextConfig } from 'next'

const nextConfig: NextConfig = {
  async rewrites() {
    return [
      {
        source: '/api/fermentation/:path*',
        destination: 'http://localhost:8000/api/:path*',
      },
      {
        source: '/api/winery/:path*',
        destination: 'http://localhost:8001/api/:path*',
      },
      {
        source: '/api/fruit-origin/:path*',
        destination: 'http://localhost:8002/api/:path*',
      },
      {
        source: '/api/analysis/:path*',
        destination: 'http://localhost:8003/api/:path*',
      },
    ]
  },
}

export default nextConfig
