/** @type {import('next').NextConfig} */
const nextConfig = {
  output: 'standalone',
  rewrites() {
    const fermentationApiUrl =
      process.env.INTERNAL_FERMENTATION_API_URL ?? 'http://localhost:8000'
    const wineryApiUrl =
      process.env.INTERNAL_WINERY_API_URL ?? 'http://localhost:8001'
    const fruitOriginApiUrl =
      process.env.INTERNAL_FRUIT_ORIGIN_API_URL ?? 'http://localhost:8002'
    const analysisApiUrl =
      process.env.INTERNAL_ANALYSIS_API_URL ?? 'http://localhost:8003'

    return [
      {
        source: '/api/fermentation/:path*',
        destination: `${fermentationApiUrl}/:path*`,
      },
      {
        source: '/api/winery/:path*',
        destination: `${wineryApiUrl}/:path*`,
      },
      {
        source: '/api/fruit-origin/:path*',
        destination: `${fruitOriginApiUrl}/:path*`,
      },
      {
        source: '/api/analysis/:path*',
        destination: `${analysisApiUrl}/:path*`,
      },
    ]
  },
}

export default nextConfig
