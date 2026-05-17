import { View, Text, StyleSheet, ScrollView, TouchableOpacity, TextInput, Alert } from 'react-native'
import { useState } from 'react'
import { useAuth } from '@clerk/clerk-expo'

const INTENSITY_OPTIONS = ['LOW', 'MEDIUM', 'HIGH', 'OVERWHELMING'] as const
const TRIGGER_TAGS = ['stress', 'anxiety', 'boredom', 'social-event', 'after-meal', 'coffee', 'morning-routine', 'loneliness']

export default function TrackScreen() {
  const [tab, setTab] = useState<'craving' | 'use'>('craving')
  const [intensity, setIntensity] = useState<typeof INTENSITY_OPTIONS[number]>('MEDIUM')
  const [triggered, setTriggered] = useState(false)
  const [mood, setMood] = useState(5)
  const [tags, setTags] = useState<string[]>([])
  const [notes, setNotes] = useState('')
  const [loading, setLoading] = useState(false)
  const { getToken } = useAuth()

  const toggleTag = (tag: string) => {
    setTags((prev) => prev.includes(tag) ? prev.filter((t) => t !== tag) : [...prev, tag])
  }

  const handleLog = async () => {
    setLoading(true)
    try {
      const token = await getToken()
      const endpoint = tab === 'craving' ? '/api/v1/cravings' : '/api/v1/usage'
      const body = tab === 'craving'
        ? { substanceType: 'NICOTINE', intensity, triggered, triggerTags: tags, mood, notes: notes || null }
        : { substanceType: 'NICOTINE', amount: 1, mood, triggerTags: tags, notes: notes || null }

      await fetch(`${process.env.EXPO_PUBLIC_API_URL}${endpoint}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
        body: JSON.stringify(body),
      })
      Alert.alert('✓ Logged', tab === 'craving' ? 'Craving recorded.' : 'Use recorded. No shame — just data.')
      setNotes('')
      setTags([])
    } finally {
      setLoading(false)
    }
  }

  return (
    <ScrollView style={styles.container} contentContainerStyle={styles.content}>
      <Text style={styles.pageTitle}>Track</Text>

      <View style={styles.tabs}>
        <TouchableOpacity style={[styles.tab, tab === 'craving' && styles.tabActive]} onPress={() => setTab('craving')}>
          <Text style={[styles.tabText, tab === 'craving' && styles.tabTextActive]}>⚡ Craving</Text>
        </TouchableOpacity>
        <TouchableOpacity style={[styles.tab, tab === 'use' && styles.tabActive]} onPress={() => setTab('use')}>
          <Text style={[styles.tabText, tab === 'use' && styles.tabTextActive]}>📝 Used</Text>
        </TouchableOpacity>
      </View>

      {tab === 'craving' && (
        <>
          <Text style={styles.label}>Intensity</Text>
          <View style={styles.intensityRow}>
            {INTENSITY_OPTIONS.map((i) => (
              <TouchableOpacity
                key={i}
                style={[styles.intensityBtn, intensity === i && styles.intensityBtnActive]}
                onPress={() => setIntensity(i)}
              >
                <Text style={[styles.intensityText, intensity === i && styles.intensityTextActive]}>{i}</Text>
              </TouchableOpacity>
            ))}
          </View>

          <Text style={styles.label}>Did you use?</Text>
          <View style={styles.row}>
            <TouchableOpacity style={[styles.yesNoBtn, !triggered && styles.beatBtn]} onPress={() => setTriggered(false)}>
              <Text style={styles.yesNoText}>Beat it 💪</Text>
            </TouchableOpacity>
            <TouchableOpacity style={[styles.yesNoBtn, triggered && styles.usedBtn]} onPress={() => setTriggered(true)}>
              <Text style={styles.yesNoText}>Used 😔</Text>
            </TouchableOpacity>
          </View>
        </>
      )}

      <Text style={styles.label}>Mood: {mood}/10</Text>
      <View style={styles.moodRow}>
        {Array.from({ length: 10 }, (_, i) => (
          <TouchableOpacity key={i} style={[styles.moodBtn, mood === i + 1 && styles.moodBtnActive]} onPress={() => setMood(i + 1)}>
            <Text style={[styles.moodBtnText, mood === i + 1 && styles.moodBtnTextActive]}>{i + 1}</Text>
          </TouchableOpacity>
        ))}
      </View>

      <Text style={styles.label}>Triggers</Text>
      <View style={styles.chips}>
        {TRIGGER_TAGS.map((tag) => (
          <TouchableOpacity key={tag} style={[styles.chip, tags.includes(tag) && styles.chipActive]} onPress={() => toggleTag(tag)}>
            <Text style={[styles.chipText, tags.includes(tag) && styles.chipTextActive]}>{tag}</Text>
          </TouchableOpacity>
        ))}
      </View>

      <Text style={styles.label}>Notes</Text>
      <TextInput
        style={styles.textInput}
        multiline
        numberOfLines={3}
        placeholder="What happened?"
        value={notes}
        onChangeText={setNotes}
      />

      <TouchableOpacity style={[styles.logBtn, loading && styles.logBtnDisabled]} onPress={handleLog} disabled={loading}>
        <Text style={styles.logBtnText}>{loading ? 'Logging...' : 'Log It'}</Text>
      </TouchableOpacity>
    </ScrollView>
  )
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#f9fafb' },
  content: { padding: 20, paddingTop: 60, paddingBottom: 40 },
  pageTitle: { fontSize: 28, fontWeight: 'bold', color: '#111827', marginBottom: 20 },
  tabs: { flexDirection: 'row', gap: 8, marginBottom: 20 },
  tab: { flex: 1, padding: 12, borderRadius: 10, backgroundColor: 'white', alignItems: 'center', borderWidth: 2, borderColor: '#e5e7eb' },
  tabActive: { borderColor: '#22c55e', backgroundColor: '#f0fdf4' },
  tabText: { fontSize: 14, fontWeight: '600', color: '#6b7280' },
  tabTextActive: { color: '#15803d' },
  label: { fontSize: 15, fontWeight: '600', color: '#374151', marginBottom: 8, marginTop: 16 },
  intensityRow: { flexDirection: 'row', gap: 8 },
  intensityBtn: { flex: 1, padding: 10, borderRadius: 8, borderWidth: 2, borderColor: '#e5e7eb', alignItems: 'center' },
  intensityBtnActive: { borderColor: '#22c55e', backgroundColor: '#f0fdf4' },
  intensityText: { fontSize: 11, fontWeight: '600', color: '#6b7280' },
  intensityTextActive: { color: '#15803d' },
  row: { flexDirection: 'row', gap: 12 },
  yesNoBtn: { flex: 1, padding: 14, borderRadius: 12, borderWidth: 2, borderColor: '#e5e7eb', alignItems: 'center' },
  beatBtn: { borderColor: '#22c55e', backgroundColor: '#f0fdf4' },
  usedBtn: { borderColor: '#f87171', backgroundColor: '#fef2f2' },
  yesNoText: { fontSize: 15, fontWeight: '600', color: '#374151' },
  moodRow: { flexDirection: 'row', gap: 4 },
  moodBtn: { width: 28, height: 28, borderRadius: 14, backgroundColor: '#e5e7eb', alignItems: 'center', justifyContent: 'center' },
  moodBtnActive: { backgroundColor: '#22c55e' },
  moodBtnText: { fontSize: 11, fontWeight: '600', color: '#6b7280' },
  moodBtnTextActive: { color: 'white' },
  chips: { flexDirection: 'row', flexWrap: 'wrap', gap: 8 },
  chip: { paddingHorizontal: 12, paddingVertical: 6, borderRadius: 16, backgroundColor: '#e5e7eb' },
  chipActive: { backgroundColor: '#fee2e2' },
  chipText: { fontSize: 13, color: '#374151' },
  chipTextActive: { color: '#dc2626', fontWeight: '600' },
  textInput: { borderWidth: 1, borderColor: '#d1d5db', borderRadius: 12, padding: 12, fontSize: 15, backgroundColor: 'white', textAlignVertical: 'top', minHeight: 80 },
  logBtn: { backgroundColor: '#16a34a', borderRadius: 12, padding: 16, alignItems: 'center', marginTop: 24 },
  logBtnDisabled: { opacity: 0.6 },
  logBtnText: { color: 'white', fontSize: 16, fontWeight: '700' },
})
