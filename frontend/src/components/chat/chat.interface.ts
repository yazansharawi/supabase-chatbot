export interface Message {
    id: string
    type: "user" | "bot"
    content: string
    timestamp: Date
    queryResult?: Record<string, unknown> | null
    isTyping?: boolean
  }
  
  export interface ChatInterfaceProps {
    config: {
      supabaseUrl: string
      supabaseKey: string
      openaiKey: string
    }
  }
  