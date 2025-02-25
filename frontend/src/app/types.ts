export interface Message {
  role: 'user' | 'assistant'
  content: string
  images?: Array<{
    base64: string
    caption: string
  }>
}

export interface ChatResponse {
  role: 'assistant'
  content: string
  images?: Array<{
    base64: string
    caption: string
  }>
}
