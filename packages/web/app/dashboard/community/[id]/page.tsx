'use client'

import useSWR from 'swr'
import Link from 'next/link'
import { useParams } from 'next/navigation'
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

interface Comment {
  id: string
  anonymousAlias: string
  content: string
  likes: number
  createdAt: string
}

export default function CommunityPostPage() {
  const params = useParams()
  const id = params.id as string

  const { data: postData, mutate: mutatePost } = useSWR<{ data: Post }>(
    `/api/v1/community/posts/${id}`,
    fetcher
  )
  const { data: commentsData, mutate: mutateComments } = useSWR<{ data: Comment[] }>(
    `/api/v1/community/posts/${id}/comments`,
    fetcher
  )

  const post = postData?.data ?? null
  const comments = commentsData?.data ?? []

  const [commentText, setCommentText] = useState('')
  const [posting, setPosting] = useState(false)

  const handlePostComment = async () => {
    if (!commentText.trim()) return
    setPosting(true)
    try {
      await fetch(`/api/v1/community/posts/${id}/comments`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ content: commentText }),
      })
      setCommentText('')
      await Promise.all([mutatePost(), mutateComments()])
    } finally {
      setPosting(false)
    }
  }

  const handleLike = async () => {
    await fetch(`/api/v1/community/posts/${id}/like`, { method: 'POST' })
    await mutatePost()
  }

  if (!post) {
    return (
      <div className="space-y-6">
        <Link href="/dashboard/community" className="inline-flex items-center gap-1 text-sm text-gray-500 hover:text-gray-700">
          ← Back
        </Link>
        <div className="bg-white rounded-2xl p-8 shadow-sm text-center text-gray-400 text-sm">
          Loading post...
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <Link href="/dashboard/community" className="inline-flex items-center gap-1 text-sm text-gray-500 hover:text-gray-700">
        ← Back to Community
      </Link>

      <div className="bg-white rounded-2xl p-6 shadow-sm">
        <div className="flex items-center gap-2 mb-3">
          <span className="text-xs font-medium text-green-600 bg-green-50 px-2 py-1 rounded-full">
            {post.anonymousAlias}
          </span>
          <span className="text-xs text-gray-400">
            {formatDistanceToNow(new Date(post.createdAt))} ago
          </span>
        </div>
        <h1 className="text-2xl font-bold text-gray-900 mb-3">{post.title}</h1>
        <p className="text-gray-700 text-sm leading-relaxed">{post.content}</p>
        <div className="flex gap-4 mt-5 text-sm text-gray-500">
          <button
            onClick={handleLike}
            className="flex items-center gap-1 hover:text-red-500 transition-colors"
          >
            ❤️ {post.likes}
          </button>
          <span className="flex items-center gap-1">💬 {post.commentCount}</span>
        </div>
      </div>

      <div className="space-y-4">
        <h2 className="text-lg font-semibold text-gray-900">Comments ({comments.length})</h2>

        {comments.map((comment) => (
          <div key={comment.id} className="bg-white rounded-2xl p-5 shadow-sm">
            <div className="flex items-center gap-2 mb-2">
              <span className="text-xs font-medium text-green-600 bg-green-50 px-2 py-1 rounded-full">
                {comment.anonymousAlias}
              </span>
              <span className="text-xs text-gray-400">
                {formatDistanceToNow(new Date(comment.createdAt))} ago
              </span>
            </div>
            <p className="text-gray-700 text-sm leading-relaxed">{comment.content}</p>
          </div>
        ))}

        {comments.length === 0 && (
          <div className="text-center py-8 text-gray-400 text-sm">
            No comments yet. Be the first to reply.
          </div>
        )}
      </div>

      <div className="bg-white rounded-2xl p-6 shadow-sm space-y-4">
        <h2 className="text-sm font-semibold text-gray-700">Add a comment</h2>
        <textarea
          value={commentText}
          onChange={(e) => setCommentText(e.target.value)}
          placeholder="Share your thoughts or offer support..."
          rows={4}
          className="w-full p-3 border border-gray-200 rounded-xl text-sm resize-none focus:outline-none focus:ring-2 focus:ring-green-500"
        />
        <button
          onClick={handlePostComment}
          disabled={!commentText.trim() || posting}
          className="w-full py-2 bg-green-600 text-white rounded-xl text-sm font-medium hover:bg-green-700 disabled:opacity-50 transition-colors"
        >
          {posting ? 'Posting...' : 'Post'}
        </button>
      </div>
    </div>
  )
}
