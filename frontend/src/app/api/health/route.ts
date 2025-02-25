import { NextResponse } from 'next/server'

interface HealthStatus {
  status: string;
  [key: string]: unknown;
}

// Add static cache with TTL
const cache: {
  status: HealthStatus | null;
  timestamp: number;
  ttl: number;
} = {
  status: null,
  timestamp: 0,
  ttl: 5 * 60 * 1000 // 5 minutes
}

export const GET = async () => {
  // Return cached response if valid
  if (cache.status && Date.now() - cache.timestamp < cache.ttl) {
    return NextResponse.json(cache.status)
  }

  try {
    const apiUrl = process.env.NODE_ENV === 'production'
      ? process.env.PROD_API_URL
      : process.env.DEV_API_URL

    if (!apiUrl) {
      throw new Error('API URL not configured')
    }

    const response = await fetch(`${apiUrl}/api/health`, {
      method: 'GET',
      headers: { 'Content-Type': 'application/json' },
      cache: 'no-store'
    }).then(res => res.json())

    // Update cache
    cache.status = response
    cache.timestamp = Date.now()

    return NextResponse.json(response)
  } catch (error) {
    console.error('Health check error:', error)
    return NextResponse.json({ status: 'error' }, { status: 503 })
  }
}

// Add OPTIONS handler to prevent CORS issues
export const OPTIONS = async () => {
  return new Response(null, {
    status: 204,
  })
}
