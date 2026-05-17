import { View, Text, TouchableOpacity, StyleSheet, ScrollView } from 'react-native'
import { useState } from 'react'
import { useRouter } from 'expo-router'
import { useAuth } from '@clerk/clerk-expo'

const STEPS = 6

const MOTIVATIONS = ['Health', 'Save Money', 'Family', 'Sports', 'Work', 'Relationships', 'Sleep', 'Mental Clarity']

export default function OnboardingScreen() {
  const [step, setStep] = useState(1)
  const [substance, setSubstance] = useState<'NICOTINE' | 'CANNABIS' | 'BOTH'>('NICOTINE')
  const [goal, setGoal] = useState<'QUIT_COMPLETELY' | 'TOLERANCE_BREAK' | 'CUT_BACK' | 'UNDECIDED'>('QUIT_COMPLETELY')
  const [motivations, setMotivations] = useState<string[]>([])
  const [notifications, setNotifications] = useState(true)
  const [loading, setLoading] = useState(false)
  const router = useRouter()

  const toggleMotivation = (m: string) => {
    setMotivations((prev) => prev.includes(m) ? prev.filter((x) => x !== m) : [...prev, m])
  }

  const handleComplete = async () => {
    setLoading(true)
    try {
      await fetch(`${process.env.EXPO_PUBLIC_API_URL}/api/v1/users/onboarding`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          step: 6,
          substanceType: substance,
          quitGoal: goal,
          timezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
          motivations,
          notificationsEnabled: notifications,
        }),
      })
      router.replace('/(tabs)/home')
    } finally {
      setLoading(false)
    }
  }

  return (
    <ScrollView style={styles.container} contentContainerStyle={styles.content}>
      {/* Step indicator */}
      <View style={styles.steps}>
        {Array.from({ length: STEPS }, (_, i) => (
          <View key={i} style={[styles.stepDot, i + 1 <= step && styles.stepDotActive]} />
        ))}
      </View>

      {step === 1 && (
        <View style={styles.stepContent}>
          <Text style={styles.title}>What do you want to quit?</Text>
          {([
            { value: 'NICOTINE' as const, emoji: '🚭', label: 'Vaping / Nicotine' },
            { value: 'CANNABIS' as const, emoji: '🌿', label: 'Cannabis / Weed' },
            { value: 'BOTH' as const, emoji: '🚭🌿', label: 'Both' },
          ]).map((opt) => (
            <TouchableOpacity
              key={opt.value}
              style={[styles.option, substance === opt.value && styles.optionSelected]}
              onPress={() => setSubstance(opt.value)}
            >
              <Text style={styles.optionEmoji}>{opt.emoji}</Text>
              <Text style={styles.optionLabel}>{opt.label}</Text>
            </TouchableOpacity>
          ))}
          <TouchableOpacity style={styles.button} onPress={() => setStep(2)}>
            <Text style={styles.buttonText}>Next →</Text>
          </TouchableOpacity>
        </View>
      )}

      {step === 2 && (
        <View style={styles.stepContent}>
          <Text style={styles.title}>What's your quit goal?</Text>
          {([
            { value: 'QUIT_COMPLETELY' as const, label: 'Quit completely' },
            { value: 'TOLERANCE_BREAK' as const, label: 'Tolerance break' },
            { value: 'CUT_BACK' as const, label: 'Cut back' },
            { value: 'UNDECIDED' as const, label: 'Not sure yet' },
          ]).map((opt) => (
            <TouchableOpacity
              key={opt.value}
              style={[styles.option, goal === opt.value && styles.optionSelected]}
              onPress={() => setGoal(opt.value)}
            >
              <Text style={styles.optionLabel}>{opt.label}</Text>
            </TouchableOpacity>
          ))}
          <View style={styles.row}>
            <TouchableOpacity style={styles.buttonSecondary} onPress={() => setStep(1)}>
              <Text style={styles.buttonSecondaryText}>Back</Text>
            </TouchableOpacity>
            <TouchableOpacity style={styles.button} onPress={() => setStep(3)}>
              <Text style={styles.buttonText}>Next →</Text>
            </TouchableOpacity>
          </View>
        </View>
      )}

      {step === 3 && (
        <View style={styles.stepContent}>
          <Text style={styles.title}>Set your quit date</Text>
          <TouchableOpacity style={styles.option} onPress={() => setStep(4)}>
            <Text style={styles.optionLabel}>🗓️ Start today</Text>
          </TouchableOpacity>
          <View style={styles.row}>
            <TouchableOpacity style={styles.buttonSecondary} onPress={() => setStep(2)}>
              <Text style={styles.buttonSecondaryText}>Back</Text>
            </TouchableOpacity>
            <TouchableOpacity style={styles.button} onPress={() => setStep(4)}>
              <Text style={styles.buttonText}>Next →</Text>
            </TouchableOpacity>
          </View>
        </View>
      )}

      {step === 4 && (
        <View style={styles.stepContent}>
          <Text style={styles.title}>What motivates you?</Text>
          <Text style={styles.subtitle}>Select all that apply</Text>
          <View style={styles.chips}>
            {MOTIVATIONS.map((m) => (
              <TouchableOpacity
                key={m}
                style={[styles.chip, motivations.includes(m) && styles.chipSelected]}
                onPress={() => toggleMotivation(m)}
              >
                <Text style={[styles.chipText, motivations.includes(m) && styles.chipTextSelected]}>{m}</Text>
              </TouchableOpacity>
            ))}
          </View>
          <View style={styles.row}>
            <TouchableOpacity style={styles.buttonSecondary} onPress={() => setStep(3)}>
              <Text style={styles.buttonSecondaryText}>Back</Text>
            </TouchableOpacity>
            <TouchableOpacity style={[styles.button, motivations.length === 0 && styles.buttonDisabled]} onPress={() => setStep(5)} disabled={motivations.length === 0}>
              <Text style={styles.buttonText}>Next →</Text>
            </TouchableOpacity>
          </View>
        </View>
      )}

      {step === 5 && (
        <View style={styles.stepContent}>
          <Text style={styles.title}>Enable notifications?</Text>
          <Text style={styles.subtitle}>Get craving predictions 30 minutes early. Turn off anytime.</Text>
          <TouchableOpacity style={[styles.option, notifications && styles.optionSelected]} onPress={() => setNotifications(true)}>
            <Text style={styles.optionLabel}>⚡ Yes, warn me before cravings</Text>
          </TouchableOpacity>
          <TouchableOpacity style={[styles.option, !notifications && styles.optionSelected]} onPress={() => setNotifications(false)}>
            <Text style={styles.optionLabel}>Skip for now</Text>
          </TouchableOpacity>
          <TouchableOpacity
            style={[styles.button, loading && styles.buttonDisabled]}
            onPress={handleComplete}
            disabled={loading}
          >
            <Text style={styles.buttonText}>{loading ? 'Setting up...' : 'Start My Recovery →'}</Text>
          </TouchableOpacity>
        </View>
      )}
    </ScrollView>
  )
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#f9fafb' },
  content: { padding: 24, paddingTop: 60 },
  steps: { flexDirection: 'row', gap: 6, marginBottom: 32 },
  stepDot: { flex: 1, height: 4, borderRadius: 2, backgroundColor: '#e5e7eb' },
  stepDotActive: { backgroundColor: '#22c55e' },
  stepContent: { gap: 12 },
  title: { fontSize: 24, fontWeight: 'bold', color: '#111827', marginBottom: 4 },
  subtitle: { fontSize: 14, color: '#6b7280', marginBottom: 8 },
  option: { borderWidth: 2, borderColor: '#e5e7eb', borderRadius: 12, padding: 16, flexDirection: 'row', alignItems: 'center', gap: 12, backgroundColor: 'white' },
  optionSelected: { borderColor: '#22c55e', backgroundColor: '#f0fdf4' },
  optionEmoji: { fontSize: 24 },
  optionLabel: { fontSize: 16, fontWeight: '500', color: '#111827' },
  button: { backgroundColor: '#16a34a', borderRadius: 12, padding: 16, alignItems: 'center', flex: 1 },
  buttonDisabled: { opacity: 0.5 },
  buttonText: { color: 'white', fontSize: 16, fontWeight: '600' },
  buttonSecondary: { borderWidth: 2, borderColor: '#e5e7eb', borderRadius: 12, padding: 16, alignItems: 'center', flex: 1 },
  buttonSecondaryText: { color: '#374151', fontSize: 16, fontWeight: '600' },
  row: { flexDirection: 'row', gap: 12, marginTop: 8 },
  chips: { flexDirection: 'row', flexWrap: 'wrap', gap: 8 },
  chip: { borderWidth: 2, borderColor: '#e5e7eb', borderRadius: 20, paddingHorizontal: 14, paddingVertical: 8 },
  chipSelected: { borderColor: '#22c55e', backgroundColor: '#f0fdf4' },
  chipText: { fontSize: 14, color: '#374151' },
  chipTextSelected: { color: '#15803d', fontWeight: '600' },
})
