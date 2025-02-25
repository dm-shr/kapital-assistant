import * as React from "react"

import { cn } from "@/lib/utils"

export function VisuallyHidden({
  className,
  ...props
}: React.HTMLAttributes<HTMLSpanElement>) {
  return (
    <span
      className={cn(
        "absolute h-px w-px p-0 -m-px overflow-hidden whitespace-nowrap border-0",
        className
      )}
      {...props}
    />
  )
}
