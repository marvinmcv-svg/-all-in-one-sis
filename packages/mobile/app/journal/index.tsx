import { View, Text, StyleSheet, FlatList, TouchableOpacity } from 'react-native'
import { useAuth } from '@clerk/clerk-expo'
import { useState, useEffect, useCallback } from 'react'
import { useRouter } from 'expo-router'

interface JournalEntry {
  id: string
  title: string | null
  content: string
  mood: number
  createdAt: string
}

export default function JournalListScreen() {
  const [entries, setEntries] = useState<JournalEntry[]>([])
  const { getToken } = useAuth()
  const router = useRouter()

  const fetchEntries = useCallback(async () => {
    try {
      const token = await getToken()
      const res = await fetch(`${process.env['EXPO_PUBLIC_API_URL']}/api/v1/journal`, {
        headers: { Authorization: `Bearer ${token}` },
      })
      const data = await res.json() as { data: JournalEntry[] }
      setEntries(data.data ?? [])
    } catch {}
  }, [getToken])

  useEffect(() => { void fetchEntries() }, [fetchEntries])

  return (
    <View style={styles.container}>
      <View style={styles.header}>
        <Text style={styles.title}>Journal</Text>
        <TouchableOpacity style={styles.addBtn} onPress={() => router.push('/journal/new')}>
          <Text style={styles.addBtnText}>+ New</Text>
        </TouchableOpacity>
      </View>
      <FlatList
        data={entries}
        keyExtractor={(item) => item.id}
        contentContainerStyle={styles.list}
        ListEmptyComponent={
          <View style={styles.empty}>
            <Text style={styles.emptyText}>No journal entries yet. How are you feeling today?</Text>
          </View>
        }
        renderItem={({ item }) => (
          <TouchableOpacity style={styles.card} onPress={() => router.push(`/journal/${item.id}`)}>
            <Text style={styles.cardTitle}>{item.title ?? 'Untitled'}</Text>
            <Text style={styles.cardContent} numberOfLines={2}>{item.content}</Text>
            <Text style={styles.cardMeta}>Mood: {item.mood}/10 · {new Date(item.createdAt).toLocaleDateString()}</Text>
          </TouchableOpacity>
        )}
      />
    </View>
  )
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#f9fafb' },
  header: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', paddingHorizontal: 20, paddingTop: 60, paddingBottom: 16 },
  title: { fontSize: 22, fontWeight: 'bold', color: '#111827' },
  addBtn: { backgroundColor: '#16a34a', borderRadius: 8, paddingHorizontal: 14, paddingVertical: 8 },
  addBtnText: { color: 'white', fontSize: 14, fontWeight: '600' },
  list: { padding: 16, gap: 12, paddingBottom: 40 },
  empty: { paddingVertical: 48, alignItems: 'center' },
  emptyText: { color: '#9ca3af', fontSize: 15, textAlign: 'center' },
  card: { backgroundColor: 'white', borderRadius: 16, padding: 16 },
  cardTitle: { fontSize: 16, fontWeight: '700', color: '#111827', marginBottom: 4 },
  cardContent: { fontSize: 14, color: '#4b5563', lineHeight: 20 },
  cardMeta: { fontSize: 12, color: '#9ca3af', marginTop: 8 },
})
