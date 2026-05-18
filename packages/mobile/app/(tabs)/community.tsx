import { View, Text, StyleSheet, FlatList, TouchableOpacity, RefreshControl } from 'react-native'
import { useState, useEffect, useCallback } from 'react'
import { useAuth } from '@clerk/clerk-expo'

interface Post {
  id: string
  anonymousAlias: string
  title: string
  content: string
  likes: number
  commentCount: number
  createdAt: string
}

export default function CommunityScreen() {
  const [posts, setPosts] = useState<Post[]>([])
  const [refreshing, setRefreshing] = useState(false)
  const { getToken } = useAuth()

  const fetchPosts = useCallback(async () => {
    try {
      const token = await getToken()
      const res = await fetch(`${process.env['EXPO_PUBLIC_API_URL']}/api/v1/community/posts`, {
        headers: { Authorization: `Bearer ${token}` },
      })
      const data = await res.json() as { data: Post[] }
      setPosts(data.data ?? [])
    } catch {}
  }, [getToken])

  useEffect(() => { void fetchPosts() }, [fetchPosts])

  const onRefresh = async () => {
    setRefreshing(true)
    await fetchPosts()
    setRefreshing(false)
  }

  return (
    <View style={styles.container}>
      <View style={styles.header}>
        <Text style={styles.title}>Community</Text>
        <Text style={styles.subtitle}>Anonymous support. Real connection.</Text>
      </View>
      <FlatList
        data={posts}
        keyExtractor={(item) => item.id}
        refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} />}
        contentContainerStyle={styles.list}
        ListEmptyComponent={
          <View style={styles.empty}>
            <Text style={styles.emptyText}>No posts yet. Be the first to share.</Text>
          </View>
        }
        renderItem={({ item }) => (
          <View style={styles.card}>
            <View style={styles.cardHeader}>
              <Text style={styles.alias}>{item.anonymousAlias}</Text>
              <Text style={styles.time}>{new Date(item.createdAt).toLocaleDateString()}</Text>
            </View>
            <Text style={styles.cardTitle}>{item.title}</Text>
            <Text style={styles.cardContent} numberOfLines={3}>{item.content}</Text>
            <View style={styles.cardFooter}>
              <Text style={styles.stat}>❤️ {item.likes}</Text>
              <Text style={styles.stat}>💬 {item.commentCount}</Text>
            </View>
          </View>
        )}
      />
    </View>
  )
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#f9fafb' },
  header: { paddingHorizontal: 20, paddingTop: 60, paddingBottom: 16 },
  title: { fontSize: 22, fontWeight: 'bold', color: '#111827' },
  subtitle: { fontSize: 13, color: '#6b7280', marginTop: 2 },
  list: { padding: 16, gap: 12, paddingBottom: 40 },
  empty: { paddingVertical: 48, alignItems: 'center' },
  emptyText: { color: '#9ca3af', fontSize: 15 },
  card: { backgroundColor: 'white', borderRadius: 16, padding: 16 },
  cardHeader: { flexDirection: 'row', justifyContent: 'space-between', marginBottom: 8 },
  alias: { fontSize: 13, fontWeight: '600', color: '#16a34a' },
  time: { fontSize: 12, color: '#9ca3af' },
  cardTitle: { fontSize: 16, fontWeight: '700', color: '#111827', marginBottom: 6 },
  cardContent: { fontSize: 14, color: '#4b5563', lineHeight: 20 },
  cardFooter: { flexDirection: 'row', gap: 16, marginTop: 12 },
  stat: { fontSize: 13, color: '#6b7280' },
})
