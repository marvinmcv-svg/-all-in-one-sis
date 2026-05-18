import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TextInput,
  TouchableOpacity,
  KeyboardAvoidingView,
  Platform,
} from 'react-native'
import { useState, useEffect, useCallback } from 'react'
import { useLocalSearchParams, useRouter } from 'expo-router'
import { useAuth } from '@clerk/clerk-expo'
import { formatDistanceToNow } from 'date-fns'

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

export default function CommunityPostScreen() {
  const { id } = useLocalSearchParams<{ id: string }>()
  const router = useRouter()
  const { getToken } = useAuth()

  const [post, setPost] = useState<Post | null>(null)
  const [comments, setComments] = useState<Comment[]>([])
  const [newComment, setNewComment] = useState('')
  const [posting, setPosting] = useState(false)
  const [liked, setLiked] = useState(false)

  const fetchPost = useCallback(async () => {
    try {
      const token = await getToken()
      const res = await fetch(
        `${process.env['EXPO_PUBLIC_API_URL']}/api/v1/community/posts/${id}`,
        { headers: { Authorization: `Bearer ${token}` } }
      )
      const data = await res.json() as { data: Post }
      setPost(data.data)
    } catch {}
  }, [getToken, id])

  const fetchComments = useCallback(async () => {
    try {
      const token = await getToken()
      const res = await fetch(
        `${process.env['EXPO_PUBLIC_API_URL']}/api/v1/community/posts/${id}/comments`,
        { headers: { Authorization: `Bearer ${token}` } }
      )
      const data = await res.json() as { data: Comment[] }
      setComments(data.data)
    } catch {}
  }, [getToken, id])

  useEffect(() => {
    void fetchPost()
    void fetchComments()
  }, [fetchPost, fetchComments])

  const handleLike = async () => {
    if (liked || !post) return
    setLiked(true)
    setPost({ ...post, likes: post.likes + 1 })
    try {
      const token = await getToken()
      await fetch(
        `${process.env['EXPO_PUBLIC_API_URL']}/api/v1/community/posts/${id}/like`,
        {
          method: 'POST',
          headers: { Authorization: `Bearer ${token}` },
        }
      )
    } catch {
      setLiked(false)
      setPost((prev) => (prev ? { ...prev, likes: prev.likes - 1 } : prev))
    }
  }

  const handlePostComment = async () => {
    if (!newComment.trim()) return
    setPosting(true)
    try {
      const token = await getToken()
      const res = await fetch(
        `${process.env['EXPO_PUBLIC_API_URL']}/api/v1/community/posts/${id}/comments`,
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            Authorization: `Bearer ${token}`,
          },
          body: JSON.stringify({ content: newComment }),
        }
      )
      if (res.ok) {
        setNewComment('')
        await fetchComments()
      }
    } finally {
      setPosting(false)
    }
  }

  return (
    <KeyboardAvoidingView
      style={styles.outer}
      behavior={Platform.OS === 'ios' ? 'padding' : undefined}
    >
      <ScrollView style={styles.container} contentContainerStyle={styles.content} keyboardShouldPersistTaps="handled">
        <TouchableOpacity onPress={() => router.back()} style={styles.backRow}>
          <Text style={styles.back}>← Back</Text>
        </TouchableOpacity>

        {post ? (
          <View style={styles.postCard}>
            <View style={styles.postMeta}>
              <View style={styles.aliasBadge}>
                <Text style={styles.aliasText}>{post.anonymousAlias}</Text>
              </View>
              <Text style={styles.timeAgo}>
                {formatDistanceToNow(new Date(post.createdAt), { addSuffix: true })}
              </Text>
            </View>
            <Text style={styles.postTitle}>{post.title}</Text>
            <Text style={styles.postContent}>{post.content}</Text>
            <TouchableOpacity style={styles.likeRow} onPress={handleLike} activeOpacity={0.7}>
              <Text style={[styles.likeBtn, liked && styles.likeBtnActive]}>
                ♥ {post.likes}
              </Text>
            </TouchableOpacity>
          </View>
        ) : (
          <Text style={styles.loadingText}>Loading post...</Text>
        )}

        <Text style={styles.commentsHeading}>
          Comments {comments.length > 0 ? `(${comments.length})` : ''}
        </Text>

        {comments.length === 0 ? (
          <Text style={styles.noComments}>No comments yet. Be the first!</Text>
        ) : (
          comments.map((comment) => (
            <View key={comment.id} style={styles.commentCard}>
              <View style={styles.commentMeta}>
                <View style={styles.aliasBadgeSmall}>
                  <Text style={styles.aliasTextSmall}>{comment.anonymousAlias}</Text>
                </View>
                <Text style={styles.commentTime}>
                  {formatDistanceToNow(new Date(comment.createdAt), { addSuffix: true })}
                </Text>
              </View>
              <Text style={styles.commentContent}>{comment.content}</Text>
            </View>
          ))
        )}

        <View style={styles.addCommentRow}>
          <TextInput
            style={styles.commentInput}
            placeholder="Add a comment..."
            value={newComment}
            onChangeText={setNewComment}
            multiline
            textAlignVertical="top"
          />
          <TouchableOpacity
            style={[styles.postBtn, (!newComment.trim() || posting) && styles.postBtnDisabled]}
            onPress={handlePostComment}
            disabled={!newComment.trim() || posting}
          >
            <Text style={styles.postBtnText}>{posting ? '...' : 'Post'}</Text>
          </TouchableOpacity>
        </View>
      </ScrollView>
    </KeyboardAvoidingView>
  )
}

const styles = StyleSheet.create({
  outer: { flex: 1, backgroundColor: '#f9fafb' },
  container: { flex: 1 },
  content: { padding: 20, paddingTop: 60, paddingBottom: 48 },
  backRow: { marginBottom: 16 },
  back: { fontSize: 16, color: '#16a34a', fontWeight: '500' },
  postCard: {
    backgroundColor: 'white',
    borderRadius: 16,
    padding: 16,
    marginBottom: 24,
    shadowColor: '#000',
    shadowOpacity: 0.05,
    shadowRadius: 8,
    shadowOffset: { width: 0, height: 2 },
    elevation: 2,
  },
  postMeta: { flexDirection: 'row', alignItems: 'center', gap: 8, marginBottom: 10 },
  aliasBadge: {
    backgroundColor: '#dcfce7',
    borderRadius: 20,
    paddingHorizontal: 10,
    paddingVertical: 3,
  },
  aliasText: { fontSize: 13, fontWeight: '600', color: '#16a34a' },
  timeAgo: { fontSize: 13, color: '#9ca3af' },
  postTitle: { fontSize: 20, fontWeight: '700', color: '#111827', marginBottom: 8 },
  postContent: { fontSize: 15, color: '#374151', lineHeight: 24, marginBottom: 14 },
  likeRow: { flexDirection: 'row' },
  likeBtn: { fontSize: 14, color: '#9ca3af', fontWeight: '600' },
  likeBtnActive: { color: '#16a34a' },
  commentsHeading: {
    fontSize: 18,
    fontWeight: '700',
    color: '#111827',
    marginBottom: 12,
  },
  noComments: { fontSize: 14, color: '#9ca3af', marginBottom: 20 },
  commentCard: {
    backgroundColor: 'white',
    borderRadius: 12,
    padding: 14,
    marginBottom: 10,
    shadowColor: '#000',
    shadowOpacity: 0.04,
    shadowRadius: 4,
    shadowOffset: { width: 0, height: 1 },
    elevation: 1,
  },
  commentMeta: { flexDirection: 'row', alignItems: 'center', gap: 8, marginBottom: 6 },
  aliasBadgeSmall: {
    backgroundColor: '#f0fdf4',
    borderRadius: 16,
    paddingHorizontal: 8,
    paddingVertical: 2,
  },
  aliasTextSmall: { fontSize: 12, fontWeight: '600', color: '#16a34a' },
  commentTime: { fontSize: 12, color: '#9ca3af' },
  commentContent: { fontSize: 14, color: '#374151', lineHeight: 21 },
  addCommentRow: {
    flexDirection: 'row',
    alignItems: 'flex-end',
    gap: 10,
    marginTop: 16,
  },
  commentInput: {
    flex: 1,
    backgroundColor: 'white',
    borderWidth: 1,
    borderColor: '#e5e7eb',
    borderRadius: 12,
    padding: 12,
    fontSize: 14,
    color: '#111827',
    minHeight: 48,
    maxHeight: 120,
  },
  postBtn: {
    backgroundColor: '#16a34a',
    borderRadius: 12,
    paddingHorizontal: 18,
    paddingVertical: 12,
    alignItems: 'center',
    justifyContent: 'center',
  },
  postBtnDisabled: { opacity: 0.5 },
  postBtnText: { color: 'white', fontWeight: '700', fontSize: 14 },
  loadingText: { fontSize: 16, color: '#9ca3af', textAlign: 'center', marginTop: 40 },
})
