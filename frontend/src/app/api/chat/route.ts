import { NextResponse } from 'next/server'

export async function POST(request: Request) {
  try {
    let apiUrl: string
    let apiKey: string

    if (process.env.NODE_ENV === 'production') {
      apiUrl = process.env.PROD_API_URL || 'https://your-prod-api.com'
      apiKey = process.env.PROD_API_KEY || ''
    } else {
      apiUrl = process.env.DEV_API_URL || 'http://localhost:8000'
      apiKey = process.env.DEV_API_KEY || ''
    }

    if (!apiKey) {
      throw new Error(`API_KEY environment variable is not set for ${process.env.NODE_ENV} environment`)
    }

    const body = await request.json()

    const response = await fetch(`${apiUrl}/api/chat`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${apiKey}`,
      },
      body: JSON.stringify(body),
    })

    if (!response.ok) {
      throw new Error(`Backend responded with status: ${response.status}`)
    }

    const data = await response.json()
    return NextResponse.json(data)
  } catch (error) {
    console.error('Chat API error:', error)
    return NextResponse.json(
      { error: error instanceof Error ? error.message : 'Failed to process request' },
      { status: 500 }
    )
  }
}
