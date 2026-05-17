import { View, Text, StyleSheet, ScrollView, TouchableOpacity } from 'react-native'
import { useState, useEffect, useCallback } from 'react'
import { useAuth } from '@clerk/clerk-expo'
import { useRouter } from 'expo-router'

interface CBTProgress {
  completedLessons: number
  totalLessons: number
  percentComplete: number
  currentWeek: number
}

const WEEK_TITLES = [
  'Understanding Your Habit',
  'Thought Records',
  'Emotional Regulation',
  'Relapse Prevention',
  'Lifestyle Redesign',
  'Maintenance',
]

export default function CBTIndexScreen() {
  const [progress, setProgress] = useState<CBTProgress | null>(null)
  const { getToken } = useAuth()
  const router = useRouter()

  const fetchProgress = useCallback(async () => {
    try {
      const token = await getToken()
      const res = await fetch(`${process.env['EXPO_PUBLIC_API_URL']}/api/v1/cbt/progress`, {
        headers: { Authorization: `Bearer ${token}` },
      })
      const data = await res.json() as { data: CBTProgress }
      setProgress(data.data)
    } catch {}
  }, [getToken])

  useEffect(() => { void fetchProgress() }, [fetchProgress])

  return (
    <ScrollView style={styles.container} contentContainerStyle={styles.content}>
      <Text style={styles.title}>CBT Program</Text>
      <Text style={styles.subtitle}>6-week cognitive behavioral therapy</Text>

      {progress && (
        <View style={styles.progressCard}>
          <View style={styles.progressRow}>
            <Text style={styles.progressText}>{progress.completedLessons}/{progress.totalLessons} lessons</Text>
            <Text style={styles.progressPercent}>{progress.percentComplete}%</Text>
          </View>
          <View style={styles.progressBar}>
            <View style={[styles.progressFill, { width: `${progress.percentComplete}%` as `${number}%` }]} />
          </View>
          <Text style={styles.progressWeek}>Week {progress.currentWeek} of 6</Text>
        </View>
      )}

      <TouchableOpacity style={styles.todayBtn} onPress={() => router.push('/cbt/1/1')}>
        <Text style={styles.todayBtnText}>📖 Start Today's Lesson</Text>
      </TouchableOpacity>

      {WEEK_TITLES.map((title, i) => (
        <TouchableOpacity key={i} style={styles.weekCard} onPress={() => router.push(`/cbt/${i + 1}/1`)}>
          <Text style={styles.weekNumber}>Week {i + 1}</Text>
          <Text style={styles.weekTitle}>{title}</Text>
          <Text style={styles.weekArrow}>›</Text>
        </TouchableOpacity>
      ))}
    </ScrollView>
  )
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#f9fafb' },
  content: { padding: 20, paddingTop: 60, paddingBottom: 40 },
  title: { fontSize: 28, fontWeight: 'bold', color: '#111827' },
  subtitle: { fontSize: 14, color: '#6b7280', marginTop: 4, marginBottom: 20 },
  progressCard: { backgroundColor: 'white', borderRadius: 16, padding: 16, marginBottom: 20 },
  progressRow: { flexDirection: 'row', justifyContent: 'space-between', marginBottom: 8 },
  progressText: { fontSize: 14, color: '#374151' },
  progressPercent: { fontSize: 14, fontWeight: '700', color: '#16a34a' },
  progressBar: { height: 8, backgroundColor: '#e5e7eb', borderRadius: 4, marginBottom: 8 },
  progressFill: { height: 8, backgroundColor: '#22c55e', borderRadius: 4 },
  progressWeek: { fontSize: 13, color: '#6b7280' },
  todayBtn: { backgroundColor: '#16a34a', borderRadius: 12, padding: 16, alignItems: 'center', marginBottom: 16 },
  todayBtnText: { color: 'white', fontSize: 16, fontWeight: '700' },
  weekCard: { backgroundColor: 'white', borderRadius: 12, padding: 16, marginBottom: 10, flexDirection: 'row', alignItems: 'center', gap: 12 },
  weekNumber: { fontSize: 13, fontWeight: '600', color: '#16a34a', width: 56 },
  weekTitle: { flex: 1, fontSize: 15, fontWeight: '500', color: '#111827' },
  weekArrow: { fontSize: 22, color: '#9ca3af' },
})
