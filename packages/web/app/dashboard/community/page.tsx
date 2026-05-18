'use client'

import useSWR from 'swr'
import { useState } from 'react'
import { formatDistanceToNow } from 'date-fns'

const fetcher = (url: string) => fetch(url).then((r) => r.json())

interface Post {
  id: string
  anonymousAlias: string
  title: string
  content: string
  likes: number
  commentCount: number
  createdAt: string
}

export default function CommunityPage() {
  const { data, mutate } = useSWR<{ data: Post[] }>('/api/v1/community/posts', fetcher)
  const posts = data?.data ?? []
  const [showForm, setShowForm] = useState(false)
  const [title, setTitle] = useState('')
  const [content, setContent] = useState('')
  const [posting, setPosting] = useState(false)

  const handlePost = async () => {
    setPosting(true)
    try {
      await fetch('/api/v1/community/posts', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ title, content, substanceTags: [] }),
      })
      setTitle('')
      setContent('')
      setShowForm(false)
      await mutate()
    } finally {
      setPosting(false)
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Community</h1>
          <p className="text-gray-600 text-sm mt-1">Anonymous support. Real connection.</p>
        </div>
        <button
          onClick={() => setShowForm(!showForm)}
          className="px-4 py-2 bg-green-600 text-white rounded-xl font-medium hover:bg-green-700"
        >
          + New Post
        </button>
      </div>

      {showForm && (
        <div className="bg-white rounded-2xl p-6 shadow-sm space-y-4">
          <h2 className="text-lg font-semibold">Share with the community</h2>
          <input
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            placeholder="Post title"
            className="w-full p-3 border border-gray-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-green-500"
          />
          <textarea
            value={content}
            onChange={(e) => setContent(e.target.value)}
            placeholder="Share your experience, ask a question, or offer support..."
            rows={4}
            className="w-full p-3 border border-gray-200 rounded-xl text-sm resize-none focus:outline-none focus:ring-2 focus:ring-green-500"
          />
          <div className="flex gap-3">
            <button onClick={() => setShowForm(false)} className="flex-1 py-2 border-2 border-gray-200 rounded-xl text-sm font-medium">Cancel</button>
            <button
              onClick={handlePost}
              disabled={!title.trim() || !content.trim() || posting}
              className="flex-1 py-2 bg-green-600 text-white rounded-xl text-sm font-medium disabled:opacity-50"
            >
              {posting ? 'Posting...' : 'Post Anonymously'}
            </button>
          </div>
        </div>
      )}

      <div className="space-y-4">
        {posts.map((post) => (
          <div key={post.id} className="bg-white rounded-2xl p-6 shadow-sm">
            <div className="flex items-center gap-2 mb-3">
              <span className="text-xs font-medium text-green-600 bg-green-50 px-2 py-1 rounded-full">{post.anonymousAlias}</span>
              <span className="text-xs text-gray-400">{formatDistanceToNow(new Date(post.createdAt))} ago</span>
            </div>
            <h3 className="text-lg font-semibold text-gray-900 mb-2">{post.title}</h3>
            <p className="text-gray-700 text-sm leading-relaxed">{post.content}</p>
            <div className="flex gap-4 mt-4 text-sm text-gray-500">
              <button
                onClick={async () => {
                  await fetch(`/api/v1/community/posts/${post.id}/like`, { method: 'POST' })
                  await mutate()
                }}
                className="flex items-center gap-1 hover:text-red-500 transition-colors"
              >
                ❤️ {post.likes}
              </button>
              <span className="flex items-center gap-1">💬 {post.commentCount}</span>
            </div>
          </div>
        ))}
        {posts.length === 0 && (
          <div className="text-center py-16 text-gray-500">
            <div className="text-4xl mb-3">🤝</div>
            <div className="font-medium">No posts yet</div>
            <div className="text-sm mt-1">Be the first to share your journey</div>
          </div>
        )}
      </div>
    </div>
  )
}
