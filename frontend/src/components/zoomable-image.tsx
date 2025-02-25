"use client"

import Image from "next/image"
import { useState } from "react"
import { Dialog, DialogContent, DialogTrigger, DialogTitle } from "@/components/ui/dialog"
import { VisuallyHidden } from "@/components/ui/visually-hidden"

interface ZoomableImageProps {
  src: string
  alt: string
  caption: string
  width: number
  height: number
}

export function ZoomableImage({ src, alt, caption, width, height }: ZoomableImageProps) {
  const [isOpen, setIsOpen] = useState(false)

  return (
    <Dialog open={isOpen} onOpenChange={setIsOpen}>
      <DialogTrigger asChild>
        <div className="cursor-zoom-in">
          <Image
            src={src}
            alt={alt}
            width={width}
            height={height}
            className="rounded-md"
          />
          <div className="mt-1 text-xs text-gray-500">
            {caption}
          </div>
        </div>
      </DialogTrigger>
      <DialogContent className="max-w-[95vw] max-h-[95vh] w-fit h-fit p-0 overflow-hidden">
        <DialogTitle asChild>
          <VisuallyHidden>View {caption}</VisuallyHidden>
        </DialogTitle>
        <div className="relative w-full h-full overflow-auto">
          <div className="p-4">
            <div className="relative flex items-center justify-center">
              <Image
                src={src}
                alt={alt}
                width={1200}
                height={800}
                className="w-auto h-auto max-w-[85vw] max-h-[85vh] object-contain"
                quality={100}
                priority
              />
            </div>
            <div className="sticky bottom-0 left-0 right-0 mt-2 p-2 text-sm text-gray-500 text-center bg-white/95 backdrop-blur supports-[backdrop-filter]:bg-white/80">
              {caption}
            </div>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  )
}
