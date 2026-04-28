import type { NextConfig } from 'next'

const nextConfig: NextConfig = {
  async rewrites() {
    return [
      {
        source: '/api/fermentation/:path*',
        destination: 'http://localhost:8000/:path*',
      },
      {
        source: '/api/winery/:path*',
        destination: 'http://localhost:8001/:path*',
      },
      {
        source: '/api/fruit-origin/:path*',
        destination: 'http://localhost:8002/:path*',
      },
      {
        source: '/api/analysis/:path*',
        destination: 'http://localhost:8003/:path*',
      },
    ]
  },
}

export default nextConfig
