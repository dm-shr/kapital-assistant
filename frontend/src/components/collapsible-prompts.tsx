"use client"

import { useState } from "react"
import { ChevronDown, ChevronUp } from "lucide-react"
import { PromptSuggestions } from "./prompt-suggestions"
import { Button } from "./ui/button"

interface CollapsiblePromptsProps {
  onSelect: (prompt: string, autoSend?: boolean) => void
  suggestions: string[]
}

export function CollapsiblePrompts({ onSelect, suggestions }: CollapsiblePromptsProps) {
  const [isExpanded, setIsExpanded] = useState(false)

  return (
    <div className="border-t border-gray-200">
      <Button
        variant="ghost"
        onClick={() => setIsExpanded(!isExpanded)}
        className="w-full flex items-center justify-between p-2 text-sm text-gray-600 hover:text-gray-900 hover:bg-gray-50"
      >
        Example questions
        {isExpanded ? (
          <ChevronUp className="h-4 w-4" />
        ) : (
          <ChevronDown className="h-4 w-4" />
        )}
      </Button>
      <div className={`overflow-hidden transition-[max-height] duration-300 ease-in-out ${
        isExpanded ? 'max-h-[200px]' : 'max-h-0'
      }`}>
        <PromptSuggestions
          suggestions={suggestions}
          onSelect={onSelect}
        />
      </div>
    </div>
  )
}
