'use client'

import { useState, useCallback } from 'react'

interface Message {
  id: string
  role: 'user' | 'assistant'
  content: string
}

export function useAIChat(sessionId: string) {
  const [messages, setMessages] = useState<Message[]>([])
  const [isStreaming, setIsStreaming] = useState(false)

  const sendMessage = useCallback(async (text: string, messageType = 'COACHING') => {
    const userMsg: Message = { id: crypto.randomUUID(), role: 'user', content: text }
    setMessages((prev) => [...prev, userMsg])
    setIsStreaming(true)

    const assistantId = crypto.randomUUID()
    setMessages((prev) => [...prev, { id: assistantId, role: 'assistant', content: '' }])

    try {
      const res = await fetch('/api/v1/ai/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: text, sessionId, messageType }),
      })

      if (!res.body) return

      const reader = res.body.getReader()
      const decoder = new TextDecoder()

      while (true) {
        const { done, value } = await reader.read()
        if (done) break
        const chunk = decoder.decode(value)
        const lines = chunk.split('\n').filter((l) => l.startsWith('data: '))
        for (const line of lines) {
          try {
            const json = JSON.parse(line.slice(6)) as { type: string; text?: string }
            if (json.type === 'delta' && json.text) {
              setMessages((prev) =>
                prev.map((m) => m.id === assistantId ? { ...m, content: m.content + json.text! } : m)
              )
            }
          } catch {}
        }
      }
    } finally {
      setIsStreaming(false)
    }
  }, [sessionId])

  return { messages, sendMessage, isStreaming }
}
