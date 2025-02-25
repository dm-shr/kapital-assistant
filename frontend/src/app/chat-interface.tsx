"use client"

import { useState, useEffect, useRef, type KeyboardEvent } from "react"
import { Button } from "@/components/ui/button"
import { Textarea } from "@/components/ui/textarea"
import { Send } from "lucide-react"
import ReactMarkdown from "react-markdown"
import remarkGfm from "remark-gfm"
import { ZoomableImage } from "@/components/zoomable-image"
import { ServerStatus } from "@/components/server-status"
import { PROMPT_EXAMPLES } from "./constants"
import type { Message, ChatResponse } from "./types"
import { LoadingMessage } from "@/components/loading-message"
import { CollapsiblePrompts } from "@/components/collapsible-prompts"

interface ChatInterfaceProps {
  initialMessages: Message[]
}

export default function ChatInterface({ initialMessages }: ChatInterfaceProps) {
  const [input, setInput] = useState("")
  const [messages, setMessages] = useState<Message[]>(initialMessages)
  const [isLoading, setIsLoading] = useState(false)
  const messagesEndRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" })
  }, [messages])

  const handleSubmit = async (messageContent: string) => {
    if (!messageContent.trim()) return

    const userMessage: Message = {
      role: "user",
      content: messageContent,
    }

    setMessages((prev) => [...prev, userMessage])
    setInput("")
    setIsLoading(true)

    const maxRetries = 3
    let retryCount = 0

    while (retryCount < maxRetries) {
      try {
        const response = await fetch('/api/chat', {  // Changed from absolute URL to relative
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            messages: [...messages, userMessage]
          }),
        })

        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`)
        }

        const data: ChatResponse = await response.json()
        setMessages((prev) => [...prev, data])
        setIsLoading(false)
        return // Success, exit the retry loop
      } catch (error) {
        console.error(`Attempt ${retryCount + 1} failed:`, error)
        retryCount++

        if (retryCount === maxRetries) {
          setMessages((prev) => [...prev, {
            role: "assistant",
            content: "Sorry, I'm having trouble connecting to the server. Please try again in a moment."
          }])
        } else {
          // Wait before retrying (exponential backoff)
          await new Promise(resolve => setTimeout(resolve, Math.pow(2, retryCount) * 1000))
        }
      }
    }
    setIsLoading(false)
  }

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault()
      handleSubmit(input)
    }
  }

  const handleSuggestionSelect = (prompt: string) => {
    setInput(prompt)
    handleSubmit(prompt)
  }

  return (
    <div className="flex flex-col h-[calc(100vh-14rem)] sm:h-[calc(100vh-16rem)] bg-background border border-gray-200 rounded-lg overflow-hidden">
      <ServerStatus />
      <div className="flex-grow overflow-y-auto p-1.5 sm:p-3 space-y-2 sm:space-y-3">
        {messages.map((message, index) => (
          <div key={index} className={`flex flex-col ${message.role === "user" ? "items-end" : "items-start"}`}>
            <div
              className={`max-w-[85%] sm:max-w-[80%] p-1.5 sm:p-2.5 rounded-lg shadow-sm ${
                message.role === "user"
                  ? "bg-[hsl(var(--user-message-bg))] text-foreground"
                  : "bg-[hsl(var(--bot-message-bg))] text-foreground"
              }`}
            >
              <div className="prose prose-xs sm:prose-sm dark:prose-invert prose-p:leading-relaxed prose-pre:p-0 max-w-none">
                <ReactMarkdown
                  remarkPlugins={[remarkGfm]}
                  components={{
                    ol: ({...props}) => <ol className="list-decimal pl-4 my-2" {...props} />,
                    ul: ({...props}) => <ul className="list-disc pl-4 my-2" {...props} />,
                  }}
                >
                  {message.content}
                </ReactMarkdown>
              </div>
              {message.images && message.images.length > 0 && (
                <div className="mt-1 sm:mt-2 grid grid-cols-2 gap-1 sm:gap-2">
                  {message.images.map((img, imgIndex) => (
                    <div key={imgIndex} className="relative">
                      <ZoomableImage
                        src={`data:image/png;base64,${img.base64}`}
                        alt={img.caption}
                        caption={img.caption}
                        width={300}
                        height={200}
                      />
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        ))}
        {isLoading && <LoadingMessage />}
        <div ref={messagesEndRef} />
      </div>
      <div className="border-t border-gray-200">
        <CollapsiblePrompts
          suggestions={PROMPT_EXAMPLES}
          onSelect={handleSuggestionSelect}
        />
        <div className="p-1.5 sm:p-3">
          <div className="flex gap-1 sm:gap-2">
            <Textarea
              placeholder="Type your message here..."
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              className="min-h-[38px] sm:min-h-[44px] text-sm sm:text-base flex-grow resize-none"
              rows={1}
            />
            <Button
              onClick={() => handleSubmit(input)}
              size="icon"
              className="shrink-0 h-[38px] w-[38px] sm:h-[44px] sm:w-[44px]"
              data-darkreader-inline-fill="false"
              data-darkreader-inline-stroke="false"
            >
              <Send className="h-4 w-4" />
            </Button>
          </div>
        </div>
      </div>
    </div>
  )
}
