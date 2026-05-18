'use client'

import { useState, KeyboardEvent } from 'react'

interface Props {
  onSend: (text: string) => void
  disabled?: boolean
}

export function ChatInput({ onSend, disabled }: Props) {
  const [text, setText] = useState('')

  const handleSend = () => {
    if (!text.trim() || disabled) return
    onSend(text)
    setText('')
  }

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  return (
    <div className="border-t border-gray-100 p-4 flex gap-3 items-end">
      <textarea
        value={text}
        onChange={(e) => setText(e.target.value)}
        onKeyDown={handleKeyDown}
        placeholder="Share what's on your mind..."
        disabled={disabled}
        rows={2}
        className="flex-1 p-3 border border-gray-200 rounded-xl resize-none focus:outline-none focus:ring-2 focus:ring-green-500 text-sm disabled:opacity-50"
      />
      <button
        onClick={handleSend}
        disabled={!text.trim() || disabled}
        className="px-4 py-3 bg-green-600 text-white rounded-xl hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed font-medium text-sm"
      >
        Send
      </button>
    </div>
  )
}
