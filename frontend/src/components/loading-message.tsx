export function LoadingMessage() {
  return (
    <div className="flex flex-col items-start">
      <div className="max-w-[85%] sm:max-w-[80%] p-1.5 sm:p-2.5 rounded-lg shadow-sm bg-[hsl(var(--bot-message-bg))] text-foreground animate-[pulse_2s_ease-in-out_infinite]">
        <div className="flex items-center gap-2">
          <div className="text-sm">Searching for the answer...</div>
        </div>
      </div>
    </div>
  )
}
