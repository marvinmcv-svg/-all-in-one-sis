import { View, Text, StyleSheet, TextInput, TouchableOpacity, ScrollView, Alert } from 'react-native'
import { useState } from 'react'
import { useAuth } from '@clerk/clerk-expo'
import { useRouter } from 'expo-router'

export default function NewJournalScreen() {
  const [title, setTitle] = useState('')
  const [content, setContent] = useState('')
  const [mood, setMood] = useState(5)
  const [loading, setLoading] = useState(false)
  const { getToken } = useAuth()
  const router = useRouter()

  const handleSave = async () => {
    if (!content.trim()) { Alert.alert('Please write something first'); return }
    setLoading(true)
    try {
      const token = await getToken()
      await fetch(`${process.env['EXPO_PUBLIC_API_URL']}/api/v1/journal`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
        body: JSON.stringify({ title: title || null, content, mood }),
      })
      router.back()
    } finally {
      setLoading(false)
    }
  }

  return (
    <ScrollView style={styles.container} contentContainerStyle={styles.content}>
      <View style={styles.headerRow}>
        <TouchableOpacity onPress={() => router.back()}>
          <Text style={styles.back}>← Back</Text>
        </TouchableOpacity>
        <TouchableOpacity style={[styles.saveBtn, loading && styles.saveBtnDisabled]} onPress={handleSave} disabled={loading}>
          <Text style={styles.saveBtnText}>{loading ? 'Saving...' : 'Save'}</Text>
        </TouchableOpacity>
      </View>

      <TextInput style={styles.titleInput} placeholder="Title (optional)" value={title} onChangeText={setTitle} />

      <Text style={styles.moodLabel}>Mood: {mood}/10</Text>
      <View style={styles.moodRow}>
        {Array.from({ length: 10 }, (_, i) => (
          <TouchableOpacity key={i} style={[styles.moodBtn, mood === i + 1 && styles.moodBtnActive]} onPress={() => setMood(i + 1)}>
            <Text style={[styles.moodBtnText, mood === i + 1 && styles.moodBtnTextActive]}>{i + 1}</Text>
          </TouchableOpacity>
        ))}
      </View>

      <TextInput
        style={styles.contentInput}
        placeholder="How are you feeling? What's on your mind?"
        value={content}
        onChangeText={setContent}
        multiline
        textAlignVertical="top"
        autoFocus
      />
    </ScrollView>
  )
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: 'white' },
  content: { padding: 20, paddingTop: 60, paddingBottom: 40 },
  headerRow: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginBottom: 20 },
  back: { fontSize: 16, color: '#16a34a', fontWeight: '500' },
  saveBtn: { backgroundColor: '#16a34a', borderRadius: 8, paddingHorizontal: 16, paddingVertical: 8 },
  saveBtnDisabled: { opacity: 0.6 },
  saveBtnText: { color: 'white', fontWeight: '600' },
  titleInput: { fontSize: 22, fontWeight: 'bold', color: '#111827', borderBottomWidth: 1, borderBottomColor: '#f3f4f6', paddingBottom: 12, marginBottom: 16 },
  moodLabel: { fontSize: 15, fontWeight: '600', color: '#374151', marginBottom: 8 },
  moodRow: { flexDirection: 'row', gap: 4, marginBottom: 20 },
  moodBtn: { width: 28, height: 28, borderRadius: 14, backgroundColor: '#e5e7eb', alignItems: 'center', justifyContent: 'center' },
  moodBtnActive: { backgroundColor: '#22c55e' },
  moodBtnText: { fontSize: 11, fontWeight: '600', color: '#6b7280' },
  moodBtnTextActive: { color: 'white' },
  contentInput: { fontSize: 16, color: '#374151', lineHeight: 26, minHeight: 300 },
})
