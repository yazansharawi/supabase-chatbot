"use client"
import { useState, useRef, useEffect, useCallback } from "react"
import { motion, AnimatePresence } from "framer-motion"
import { Button } from "@/components/ui/button"
import { Card, CardContent } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { ScrollArea } from "@/components/ui/scroll-area"
import { Send, Bot, User, Loader2 } from "@/lib/icons"
import {ChatInterfaceProps, Message} from "./chat.interface"

export function ChatInterface({ config }: ChatInterfaceProps) {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: "welcome",
      type: "bot",
      content: "Hello! I'm your Supabase database assistant. You can ask me questions about your data using natural language. Try asking 'What tables do I have?' to get started, or ask about counting, viewing, or filtering your data.",
      timestamp: new Date()
    }
  ])
  const [inputValue, setInputValue] = useState("")
  const [isLoading, setIsLoading] = useState(false)
  const [currentStatus, setCurrentStatus] = useState("")
  const scrollAreaRef = useRef<HTMLDivElement>(null)
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const [shouldAutoScroll, setShouldAutoScroll] = useState(true)
  const [isUserScrolling, setIsUserScrolling] = useState(false)
  const scrollStopTimeoutIdRef = useRef<number | null>(null)

  const scrollToBottom = useCallback(() => {
    if (shouldAutoScroll && !isUserScrolling) {
      messagesEndRef.current?.scrollIntoView({ behavior: "smooth" })
    }
  }, [shouldAutoScroll, isUserScrolling])

  const checkIfScrolledToBottom = () => {
    if (!scrollAreaRef.current) return
    const viewport = scrollAreaRef.current.querySelector('[data-slot="scroll-area-viewport"]') as HTMLElement | null
    if (!viewport) return
    const { scrollTop, scrollHeight, clientHeight } = viewport
    const isAtBottom = scrollHeight - scrollTop - clientHeight < 50
    setShouldAutoScroll(isAtBottom)
  }

  useEffect(() => {
    const rootEl = scrollAreaRef.current
    const viewport = rootEl?.querySelector('[data-slot="scroll-area-viewport"]') as HTMLElement | null
    if (!viewport) return

    const onScroll = () => {
      setIsUserScrolling(true)
      checkIfScrolledToBottom()

      if (scrollStopTimeoutIdRef.current) {
        window.clearTimeout(scrollStopTimeoutIdRef.current)
      }
      scrollStopTimeoutIdRef.current = window.setTimeout(() => {
        setIsUserScrolling(false)
      }, 150)
    }

    viewport.addEventListener('scroll', onScroll, { passive: true })
    return () => {
      viewport.removeEventListener('scroll', onScroll)
      if (scrollStopTimeoutIdRef.current) {
        window.clearTimeout(scrollStopTimeoutIdRef.current)
      }
    }
  }, [])

  useEffect(() => {
    scrollToBottom()
  }, [messages, shouldAutoScroll, scrollToBottom])

  const sanitizeInput = (input: string): string => {
    return input
      .replace(/[<>{}]/g, '')
      .slice(0, 500)
      .trim()
  }

  const handleSendMessage = async () => {
    if (!inputValue.trim() || isLoading) return

    const sanitizedInput = sanitizeInput(inputValue)
    
    if (!sanitizedInput) {
      return
    }

    const userMessage: Message = {
      id: Date.now().toString(),
      type: "user",
      content: sanitizedInput,
      timestamp: new Date()
    }

    setMessages(prev => [...prev, userMessage])
    const currentQuery = sanitizedInput
    setInputValue("")
    setIsLoading(true)
    setCurrentStatus("Connecting to database...")

    const botMessageId = (Date.now() + 1).toString()
    const initialBotMessage: Message = {
      id: botMessageId,
      type: "bot",
      content: "",
      timestamp: new Date(),
      isTyping: true
    }

    setMessages(prev => [...prev, initialBotMessage])

    try {
      const response = await fetch('/api/chat/stream', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          message: currentQuery,
          config: config
        }),
      })

      if (!response.ok) {
        throw new Error('Stream request failed')
      }

      const reader = response.body?.getReader()
      const decoder = new TextDecoder()
      let accumulatedContent = ""
      let queryResult: Record<string, unknown> | null = null

      if (reader) {
        while (true) {
          const { done, value } = await reader.read()
          if (done) break

          const chunk = decoder.decode(value)
          const lines = chunk.split('\n')

          for (const line of lines) {
            if (line.startsWith('data: ')) {
              try {
                const data = JSON.parse(line.slice(6))
                
                if (data.type === 'status') {
                  setCurrentStatus(data.message)
                  setMessages(prev => prev.map(msg => 
                    msg.id === botMessageId 
                      ? { ...msg, content: "", isTyping: true }
                      : msg
                  ))
                } else if (data.type === 'response_chunk') {
                  accumulatedContent += data.content
                  setMessages(prev => prev.map(msg => 
                    msg.id === botMessageId 
                      ? { ...msg, content: accumulatedContent, isTyping: false }
                      : msg
                  ))
                } else if (data.type === 'response') {
                  setMessages(prev => prev.map(msg => 
                    msg.id === botMessageId 
                      ? { ...msg, content: data.message, queryResult: data.queryResult, isTyping: false }
                      : msg
                  ))
                } else if (data.type === 'final') {
                  queryResult = data.queryResult
                  setMessages(prev => prev.map(msg => 
                    msg.id === botMessageId 
                      ? { ...msg, queryResult: queryResult, isTyping: false }
                      : msg
                  ))
                } else if (data.type === 'error') {
                  console.error('Streaming error:', data)
                  setMessages(prev => prev.map(msg => 
                    msg.id === botMessageId 
                      ? { ...msg, content: data.message || data.error || "An error occurred", isTyping: false }
                      : msg
                  ))
                  break
                } else if (data.type === 'done') {
                  setMessages(prev => prev.map(msg => 
                    msg.id === botMessageId 
                      ? { ...msg, isTyping: false }
                      : msg
                  ))
                  break
                }
              } catch (parseError) {
                console.error('Error parsing streaming data:', parseError)
              }
            }
          }
        }
      }

    } catch (error) {
      console.error('Streaming error:', error)
      setMessages(prev => prev.map(msg => 
        msg.id === botMessageId 
          ? { ...msg, content: "I'm sorry, there was an error processing your request. Please check your configuration and try again.", isTyping: false }
          : msg
      ))
    } finally {
      setIsLoading(false)
      setCurrentStatus("")
    }
  }

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSendMessage()
    }
  }

  const TypingIndicator = () => (
    <motion.div
      initial={{ opacity: 0, scale: 0.8 }}
      animate={{ opacity: 1, scale: 1 }}
      exit={{ opacity: 0, scale: 0.8 }}
      className="flex items-center gap-2 text-sm text-muted-foreground"
    >
      <Loader2 className="w-4 h-4 animate-spin" />
      <span>{currentStatus || "Processing your query..."}</span>
    </motion.div>
  )



  return (
    <div className="flex flex-col h-full">
      <Card className="flex flex-col h-full border-0 shadow-none p-0 rounded-none">
        <CardContent className="flex-1 flex flex-col p-0 min-h-0">
          <ScrollArea ref={scrollAreaRef} className="flex-1 p-4">
            <div className="space-y-4">
              <AnimatePresence mode="popLayout">
                {messages.map((message) => (
                  <motion.div
                    key={message.id}
                    initial={{ opacity: 0, y: 20, scale: 0.95 }}
                    animate={{ opacity: 1, y: 0, scale: 1 }}
                    exit={{ opacity: 0, y: -20, scale: 0.95 }}
                    transition={{ duration: 0.3, ease: "easeOut" }}
                    className={`flex gap-3 ${
                      message.type === "user" ? "justify-end" : "justify-start"
                    }`}
                  >
                    <div
                      className={`flex gap-3 max-w-[85%] ${
                        message.type === "user" ? "flex-row-reverse" : "flex-row"
                      }`}
                    >
                      <div 
                        className={`w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0 ${
                          message.type === "user" 
                            ? "bg-primary text-primary-foreground" 
                            : "supabase-gradient text-white"
                        }`}
                      >
                        {message.type === "user" ? (
                          <User className="w-4 h-4" />
                        ) : (
                          <Bot className="w-4 h-4" />
                        )}
                      </div>
                      <div
                        className={`rounded-lg p-3 shadow-sm ${
                          message.type === "user"
                            ? "bg-primary text-primary-foreground"
                            : "bg-card border border-border"
                        }`}
                      >
                        {message.isTyping ? (
                          <TypingIndicator />
                        ) : (
                          <>
                            <p className="text-sm whitespace-pre-wrap">{message.content}</p>
                            <p className="text-xs opacity-70 mt-1">
                              {message.timestamp.toLocaleTimeString()}
                            </p>
                          </>
                        )}
                      </div>
                    </div>
                  </motion.div>
                ))}
              </AnimatePresence>
              <div ref={messagesEndRef} />
            </div>
          </ScrollArea>
          <motion.div 
            className="flex-shrink-0 p-4 border-t bg-background"
            initial={{ y: 50, opacity: 0 }}
            animate={{ y: 0, opacity: 1 }}
            transition={{ duration: 0.3 }}
          >
            <div className="flex gap-2">
              <Input
                placeholder="Ask about your database..."
                value={inputValue}
                onChange={(e) => setInputValue(e.target.value)}
                onKeyPress={handleKeyPress}
                disabled={isLoading}
                className="flex-1"
              />
              <Button 
                onClick={handleSendMessage} 
                disabled={isLoading || !inputValue.trim()}
                size="icon"
              >
                {isLoading ? (
                  <Loader2 className="w-4 h-4 animate-spin" />
                ) : (
                  <Send className="w-4 h-4" />
                )}
              </Button>
            </div>
          </motion.div>
        </CardContent>
      </Card>
    </div>
  )
} 