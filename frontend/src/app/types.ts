export interface Message {
  role: 'user' | 'assistant';
  content: string;
  images?: Array<{
    base64: string;
    caption: string;
  }>;
}

export type ChatResponse = Message;
