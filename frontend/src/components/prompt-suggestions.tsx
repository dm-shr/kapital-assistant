interface PromptSuggestionsProps {
  onSelect: (prompt: string, autoSend?: boolean) => void
  suggestions: string[]
}

export function PromptSuggestions({ onSelect, suggestions }: PromptSuggestionsProps) {
  return (
    <div className="grid grid-cols-1 gap-2 p-2 overflow-y-auto max-h-[200px] scrollbar-thin scrollbar-thumb-gray-300 scrollbar-track-transparent">
      {suggestions.map((prompt, index) => (
        <button
          key={index}
          onClick={() => onSelect(prompt, true)}
          className="w-full text-left text-sm bg-white hover:bg-gray-50 text-gray-700 py-2 px-3 rounded-lg border border-gray-200 transition-colors text-ellipsis overflow-hidden shrink-0"
        >
          {prompt}
        </button>
      ))}
    </div>
  )
}
