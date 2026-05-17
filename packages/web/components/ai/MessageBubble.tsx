interface Message {
  id: string
  role: 'user' | 'assistant'
  content: string
}

export function MessageBubble({ message }: { message: Message }) {
  const isUser = message.role === 'user'
  return (
    <div className={`flex ${isUser ? 'justify-end' : 'justify-start'}`}>
      {!isUser && (
        <div className="w-8 h-8 bg-green-100 rounded-full flex items-center justify-center text-sm mr-2 flex-shrink-0">🌱</div>
      )}
      <div
        className={`max-w-[80%] px-4 py-3 rounded-2xl text-sm leading-relaxed ${
          isUser
            ? 'bg-green-600 text-white rounded-br-sm'
            : 'bg-gray-100 text-gray-900 rounded-bl-sm'
        }`}
      >
        {message.content}
      </div>
    </div>
  )
}
