import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TextInput,
  TouchableOpacity,
  Alert,
} from 'react-native'
import { useState, useEffect, useCallback } from 'react'
import { useLocalSearchParams, useRouter } from 'expo-router'
import { useAuth } from '@clerk/clerk-expo'

interface Lesson {
  id: number
  weekNumber: number
  lessonNumber: number
  title: string
  content: string
  completedAt: string | null
  responseText: string | null
  aiFeedback: string | null
}

export default function CBTLessonScreen() {
  const { weekNum, lessonNum } = useLocalSearchParams<{ weekNum: string; lessonNum: string }>()
  const router = useRouter()
  const { getToken } = useAuth()

  const weekNumber = parseInt(weekNum ?? '1', 10)
  const lessonNumber = parseInt(lessonNum ?? '1', 10)
  const lessonId = (weekNumber - 1) * 7 + (lessonNumber - 1)

  const [lesson, setLesson] = useState<Lesson | null>(null)
  const [responseText, setResponseText] = useState('')
  const [loading, setLoading] = useState(false)

  const fetchLesson = useCallback(async () => {
    try {
      const token = await getToken()
      const res = await fetch(`${process.env['EXPO_PUBLIC_API_URL']}/api/v1/cbt/program`, {
        headers: { Authorization: `Bearer ${token}` },
      })
      const data = await res.json() as { data: Lesson[] }
      const found = data.data.find(
        (l) => l.weekNumber === weekNumber && l.lessonNumber === lessonNumber
      )
      if (found) {
        setLesson(found)
        if (found.responseText) {
          setResponseText(found.responseText)
        }
      }
    } catch {}
  }, [getToken, weekNumber, lessonNumber])

  useEffect(() => { void fetchLesson() }, [fetchLesson])

  const handleSubmit = async () => {
    if (!responseText.trim()) {
      Alert.alert('Please write a response before submitting')
      return
    }
    setLoading(true)
    try {
      const token = await getToken()
      const res = await fetch(
        `${process.env['EXPO_PUBLIC_API_URL']}/api/v1/cbt/${lessonId}/complete`,
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            Authorization: `Bearer ${token}`,
          },
          body: JSON.stringify({ responseText }),
        }
      )
      if (res.ok) {
        Alert.alert('Great work! 🎉')
        await fetchLesson()
      }
    } finally {
      setLoading(false)
    }
  }

  const getNextPath = (): string | null => {
    if (weekNumber === 6 && lessonNumber === 7) return null
    if (lessonNumber < 7) return `/cbt/${weekNumber}/${lessonNumber + 1}`
    return `/cbt/${weekNumber + 1}/1`
  }

  const nextPath = getNextPath()

  return (
    <ScrollView style={styles.container} contentContainerStyle={styles.content}>
      <View style={styles.headerRow}>
        <TouchableOpacity onPress={() => router.back()}>
          <Text style={styles.back}>← Back</Text>
        </TouchableOpacity>
        <Text style={styles.weekLabel}>
          Week {weekNumber} · Day {lessonNumber}
        </Text>
      </View>

      {lesson ? (
        <>
          <Text style={styles.title}>{lesson.title}</Text>

          {lesson.completedAt && (
            <View style={styles.completedBadge}>
              <Text style={styles.completedBadgeText}>✓ Completed</Text>
            </View>
          )}

          <Text style={styles.bodyText}>{lesson.content}</Text>

          {lesson.completedAt && lesson.responseText ? (
            <View style={styles.responseDisplay}>
              <Text style={styles.responseDisplayLabel}>Your response</Text>
              <Text style={styles.responseDisplayText}>{lesson.responseText}</Text>
            </View>
          ) : null}

          {lesson.aiFeedback && lesson.completedAt ? (
            <View style={styles.feedbackCard}>
              <Text style={styles.feedbackHeading}>💡 AI Feedback</Text>
              <Text style={styles.feedbackText}>{lesson.aiFeedback}</Text>
            </View>
          ) : null}

          <Text style={styles.responseLabel}>Your response</Text>
          <TextInput
            style={styles.responseInput}
            placeholder="Write your thoughts here..."
            value={responseText}
            onChangeText={setResponseText}
            multiline
            textAlignVertical="top"
          />

          <TouchableOpacity
            style={[styles.submitBtn, loading && styles.submitBtnDisabled]}
            onPress={handleSubmit}
            disabled={loading}
          >
            <Text style={styles.submitBtnText}>
              {loading ? 'Saving...' : lesson.completedAt ? 'Update Response' : 'Complete Lesson'}
            </Text>
          </TouchableOpacity>

          {lesson.completedAt && nextPath ? (
            <TouchableOpacity
              style={styles.nextBtn}
              onPress={() => router.push(nextPath as `/${string}`)}
            >
              <Text style={styles.nextBtnText}>Next Lesson →</Text>
            </TouchableOpacity>
          ) : null}
        </>
      ) : (
        <Text style={styles.loadingText}>Loading lesson...</Text>
      )}
    </ScrollView>
  )
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: 'white' },
  content: { padding: 20, paddingTop: 60, paddingBottom: 48 },
  headerRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 24,
  },
  back: { fontSize: 16, color: '#16a34a', fontWeight: '500' },
  weekLabel: { fontSize: 14, fontWeight: '600', color: '#6b7280' },
  title: { fontSize: 24, fontWeight: 'bold', color: '#111827', marginBottom: 12 },
  completedBadge: {
    alignSelf: 'flex-start',
    backgroundColor: '#dcfce7',
    borderRadius: 20,
    paddingHorizontal: 12,
    paddingVertical: 4,
    marginBottom: 16,
  },
  completedBadgeText: { fontSize: 13, fontWeight: '600', color: '#16a34a' },
  bodyText: { fontSize: 16, color: '#4b5563', lineHeight: 26, marginBottom: 24 },
  responseDisplay: {
    backgroundColor: '#f9fafb',
    borderRadius: 12,
    padding: 14,
    marginBottom: 20,
  },
  responseDisplayLabel: { fontSize: 13, fontWeight: '600', color: '#6b7280', marginBottom: 6 },
  responseDisplayText: { fontSize: 15, color: '#374151', lineHeight: 22 },
  feedbackCard: {
    backgroundColor: '#f0fdf4',
    borderRadius: 12,
    padding: 16,
    marginBottom: 24,
    borderWidth: 1,
    borderColor: '#bbf7d0',
  },
  feedbackHeading: { fontSize: 15, fontWeight: '700', color: '#15803d', marginBottom: 8 },
  feedbackText: { fontSize: 15, color: '#166534', lineHeight: 22 },
  responseLabel: { fontSize: 15, fontWeight: '600', color: '#374151', marginBottom: 8 },
  responseInput: {
    borderWidth: 1,
    borderColor: '#e5e7eb',
    borderRadius: 12,
    padding: 14,
    fontSize: 15,
    color: '#111827',
    minHeight: 120,
    marginBottom: 16,
    backgroundColor: '#fafafa',
  },
  submitBtn: {
    backgroundColor: '#16a34a',
    borderRadius: 12,
    padding: 16,
    alignItems: 'center',
    marginBottom: 12,
  },
  submitBtnDisabled: { opacity: 0.6 },
  submitBtnText: { color: 'white', fontSize: 16, fontWeight: '700' },
  nextBtn: {
    borderWidth: 2,
    borderColor: '#16a34a',
    borderRadius: 12,
    padding: 16,
    alignItems: 'center',
  },
  nextBtnText: { color: '#16a34a', fontSize: 16, fontWeight: '700' },
  loadingText: { fontSize: 16, color: '#9ca3af', textAlign: 'center', marginTop: 40 },
})
