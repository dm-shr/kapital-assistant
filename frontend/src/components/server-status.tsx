"use client"

import { useEffect, useState, useRef } from "react"

export function ServerStatus() {
  const [isOnline, setIsOnline] = useState<boolean | null>(null)
  const checkCount = useRef(0)
  const lastCheck = useRef<number>(0)

  useEffect(() => {
    // Prevent multiple checks in development
    if (checkCount.current > 0) {
      return
    }
    checkCount.current++

    const checkHealth = async () => {
      const now = Date.now()
      // Prevent checks more frequent than every 5 seconds
      if (now - lastCheck.current < 5000) {
        return
      }
      lastCheck.current = now

      try {
        const res = await fetch('/api/health')
        setIsOnline(res.ok)
      } catch {
        setIsOnline(false)
      }
    }

    // Single initial check after delay
    const timeoutId = setTimeout(checkHealth, 5000)

    // Much less frequent interval checks
    const intervalId = setInterval(checkHealth, 1 * 60 * 1000)

    // Cleanup function
    return () => {
      clearTimeout(timeoutId)
      clearInterval(intervalId)
    }
  }, []) // Empty dependency array

  if (isOnline === null) return null

  return (
    <div className="px-2 py-1 bg-gray-100 text-xs flex justify-end items-center gap-2">
      <span>Server:</span>
      {isOnline ? (
        <span className="text-green-600">Online</span>
      ) : (
        <span className="text-red-600">Offline</span>
      )}
    </div>
  )
}
