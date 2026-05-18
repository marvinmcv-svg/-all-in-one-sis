'use client'

import { useState, useRef, useEffect } from 'react'
import { MessageBubble } from './MessageBubble'
import { ChatInput } from './ChatInput'
import { useAIChat } from '@/hooks/useAIChat'

const CRISIS_KEYWORDS = ['hurt myself', 'not worth it', 'give up', 'kill myself', 'suicidal', 'want to die']

export function ChatWindow() {
  const sessionId = useRef(crypto.randomUUID()).current
  const { messages, sendMessage, isStreaming } = useAIChat(sessionId)
  const bottomRef = useRef<HTMLDivElement>(null)
  const [showCrisis, setShowCrisis] = useState(false)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const handleSend = async (text: string) => {
    const isCrisis = CRISIS_KEYWORDS.some((kw) => text.toLowerCase().includes(kw))
    if (isCrisis) setShowCrisis(true)
    await sendMessage(text, isCrisis ? 'CRISIS' : 'COACHING')
  }

  return (
    <div className="flex flex-col flex-1 bg-white rounded-2xl shadow-sm overflow-hidden">
      {showCrisis && (
        <div className="bg-red-50 border-b border-red-200 p-4">
          <div className="font-semibold text-red-800 mb-1">If you're in crisis</div>
          <div className="text-sm text-red-700">
            Call or text <strong>988</strong> (Suicide & Crisis Lifeline) · Text HOME to <strong>741741</strong>
          </div>
        </div>
      )}

      <div className="flex-1 overflow-y-auto p-6 space-y-4">
        {messages.length === 0 && (
          <div className="text-center py-12 text-gray-500">
            <div className="text-4xl mb-3">💬</div>
            <div className="font-medium">Your AI recovery coach is here</div>
            <div className="text-sm mt-1">Share what's on your mind. No judgment, ever.</div>
          </div>
        )}
        {messages.map((msg) => (
          <MessageBubble key={msg.id} message={msg} />
        ))}
        {isStreaming && (
          <div className="flex items-center gap-2 text-gray-500 text-sm">
            <div className="flex gap-1">
              <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
              <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
              <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
            </div>
            ClearPath is typing...
          </div>
        )}
        <div ref={bottomRef} />
      </div>

      <ChatInput onSend={handleSend} disabled={isStreaming} />
    </div>
  )
}
