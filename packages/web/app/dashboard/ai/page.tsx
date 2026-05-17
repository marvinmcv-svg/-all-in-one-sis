import { ChatWindow } from '@/components/ai/ChatWindow'

export default function AICoachPage() {
  return (
    <div className="h-full flex flex-col">
      <div className="mb-4">
        <h1 className="text-2xl font-bold text-gray-900">AI Coach</h1>
        <p className="text-gray-600">Your 24/7 recovery coach. Judgment-free, always available.</p>
      </div>
      <ChatWindow />
    </div>
  )
}
