import { NextResponse } from 'next/server'

export const runtime = 'edge' // Add this line to use Edge Runtime

export async function POST(request: Request) {
  try {
    let apiUrl: string
    let apiKey: string

    if (process.env.NODE_ENV === 'production') {
      apiUrl = process.env.PROD_API_URL
      apiKey = process.env.PROD_API_KEY
    } else {
      apiUrl = process.env.DEV_API_URL
      apiKey = process.env.DEV_API_KEY
    }

    // Validate environment variables
    if (!apiUrl || !apiKey) {
      console.error('Missing environment variables:', {
        hasUrl: !!apiUrl,
        hasKey: !!apiKey,
        env: process.env.NODE_ENV
      })
      return NextResponse.json(
        { error: 'API configuration error' },
        { status: 500 }
      )
    }

    const body = await request.json()

    // Log request details (for debugging)
    console.log('Making request to:', apiUrl)

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
      {
        error: error instanceof Error ? error.message : 'Failed to process request',
        details: process.env.NODE_ENV === 'development' ? String(error) : undefined
      },
      { status: 500 }
    )
  }
}
