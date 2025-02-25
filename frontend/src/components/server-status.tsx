"use client"

import { useEffect, useState } from "react"
import { AlertCircle } from "lucide-react"

export function ServerStatus() {
  const [isServerDown, setIsServerDown] = useState(false)

  useEffect(() => {
    const checkServer = async () => {
      try {
        const response = await fetch('/api/health')
        setIsServerDown(!response.ok)
      } catch (error) {
        setIsServerDown(true)
      }
    }

    checkServer()
    const interval = setInterval(checkServer, 30000) // Check every 30 seconds
    return () => clearInterval(interval)
  }, [])

  if (!isServerDown) return null

  return (
    <div className="bg-red-50 border-l-4 border-red-400 p-4 mb-4">
      <div className="flex">
        <div className="flex-shrink-0">
          <AlertCircle className="h-5 w-5 text-red-400" />
        </div>
        <div className="ml-3">
          <p className="text-sm text-red-700">
            Server connection error. Please try again later or contact support.
          </p>
        </div>
      </div>
    </div>
  )
}
