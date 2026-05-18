import { View, Text, StyleSheet, TouchableOpacity } from 'react-native'
import { useState } from 'react'
import { useAuth } from '@clerk/clerk-expo'
import { useRouter } from 'expo-router'

const INTENSITY_OPTIONS = ['LOW', 'MEDIUM', 'HIGH', 'OVERWHELMING'] as const

export default function QuickLogModal() {
  const [intensity, setIntensity] = useState<typeof INTENSITY_OPTIONS[number]>('MEDIUM')
  const [triggered, setTriggered] = useState(false)
  const [loading, setLoading] = useState(false)
  const { getToken } = useAuth()
  const router = useRouter()

  const handleLog = async () => {
    setLoading(true)
    try {
      const token = await getToken()
      await fetch(`${process.env['EXPO_PUBLIC_API_URL']}/api/v1/cravings`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
        body: JSON.stringify({ substanceType: 'NICOTINE', intensity, triggered, triggerTags: [], mood: 5 }),
      })
      router.back()
    } finally {
      setLoading(false)
    }
  }

  return (
    <View style={styles.overlay}>
      <View style={styles.modal}>
        <View style={styles.header}>
          <Text style={styles.title}>Quick Log</Text>
          <TouchableOpacity onPress={() => router.back()}>
            <Text style={styles.close}>✕</Text>
          </TouchableOpacity>
        </View>

        <Text style={styles.label}>How intense?</Text>
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
          <TouchableOpacity style={[styles.choiceBtn, !triggered && styles.beatBtn]} onPress={() => setTriggered(false)}>
            <Text style={styles.choiceText}>Beat it 💪</Text>
          </TouchableOpacity>
          <TouchableOpacity style={[styles.choiceBtn, triggered && styles.usedBtn]} onPress={() => setTriggered(true)}>
            <Text style={styles.choiceText}>Used 😔</Text>
          </TouchableOpacity>
        </View>

        <TouchableOpacity
          style={[styles.logBtn, loading && styles.logBtnDisabled]}
          onPress={handleLog}
          disabled={loading}
        >
          <Text style={styles.logBtnText}>{loading ? 'Logging...' : 'Log It'}</Text>
        </TouchableOpacity>
      </View>
    </View>
  )
}

const styles = StyleSheet.create({
  overlay: { flex: 1, backgroundColor: 'rgba(0,0,0,0.5)', justifyContent: 'flex-end' },
  modal: { backgroundColor: 'white', borderTopLeftRadius: 24, borderTopRightRadius: 24, padding: 24, paddingBottom: 40 },
  header: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginBottom: 20 },
  title: { fontSize: 20, fontWeight: 'bold', color: '#111827' },
  close: { fontSize: 20, color: '#9ca3af' },
  label: { fontSize: 15, fontWeight: '600', color: '#374151', marginBottom: 10, marginTop: 16 },
  intensityRow: { flexDirection: 'row', gap: 8 },
  intensityBtn: { flex: 1, padding: 10, borderRadius: 8, borderWidth: 2, borderColor: '#e5e7eb', alignItems: 'center' },
  intensityBtnActive: { borderColor: '#22c55e', backgroundColor: '#f0fdf4' },
  intensityText: { fontSize: 11, fontWeight: '600', color: '#6b7280' },
  intensityTextActive: { color: '#15803d' },
  row: { flexDirection: 'row', gap: 12 },
  choiceBtn: { flex: 1, padding: 14, borderRadius: 12, borderWidth: 2, borderColor: '#e5e7eb', alignItems: 'center' },
  beatBtn: { borderColor: '#22c55e', backgroundColor: '#f0fdf4' },
  usedBtn: { borderColor: '#f87171', backgroundColor: '#fef2f2' },
  choiceText: { fontSize: 15, fontWeight: '600', color: '#374151' },
  logBtn: { backgroundColor: '#16a34a', borderRadius: 12, padding: 16, alignItems: 'center', marginTop: 24 },
  logBtnDisabled: { opacity: 0.6 },
  logBtnText: { color: 'white', fontSize: 16, fontWeight: '700' },
})
