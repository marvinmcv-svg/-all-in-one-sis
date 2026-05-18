import { View, Text, StyleSheet, ScrollView, TouchableOpacity, RefreshControl } from 'react-native'
import { useState, useEffect, useCallback } from 'react'
import { useRouter } from 'expo-router'
import { useAuth } from '@clerk/clerk-expo'

interface DashboardStats {
  daysClean: number
  secondsClean: number
  currentStreakDays: number
  moneySavedCents: number
  cravingsBeatThisWeek: number
  avgMoodThisWeek: number | null
  substanceType: string
}

export default function HomeScreen() {
  const [stats, setStats] = useState<DashboardStats | null>(null)
  const [refreshing, setRefreshing] = useState(false)
  const { getToken } = useAuth()
  const router = useRouter()

  const fetchStats = useCallback(async () => {
    try {
      const token = await getToken()
      const res = await fetch(`${process.env.EXPO_PUBLIC_API_URL}/api/v1/dashboard/stats`, {
        headers: { Authorization: `Bearer ${token}` },
      })
      const data = await res.json() as { data: DashboardStats }
      setStats(data.data)
    } catch {}
  }, [getToken])

  useEffect(() => { void fetchStats() }, [fetchStats])

  const onRefresh = async () => {
    setRefreshing(true)
    await fetchStats()
    setRefreshing(false)
  }

  const hours = stats ? Math.floor((stats.secondsClean % 86400) / 3600) : 0
  const minutes = stats ? Math.floor((stats.secondsClean % 3600) / 60) : 0

  return (
    <ScrollView
      style={styles.container}
      refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} tintColor="#16a34a" />}
    >
      <View style={styles.header}>
        <Text style={styles.logo}>🌱 ClearPath</Text>
      </View>

      {/* Clean Time Counter */}
      <View style={styles.heroCard}>
        <Text style={styles.heroLabel}>Time Clean</Text>
        <View style={styles.heroTime}>
          <View style={styles.heroUnit}>
            <Text style={styles.heroNumber}>{stats?.daysClean ?? 0}</Text>
            <Text style={styles.heroUnitLabel}>days</Text>
          </View>
          <Text style={styles.heroDivider}>:</Text>
          <View style={styles.heroUnit}>
            <Text style={styles.heroNumber}>{hours}</Text>
            <Text style={styles.heroUnitLabel}>hrs</Text>
          </View>
          <Text style={styles.heroDivider}>:</Text>
          <View style={styles.heroUnit}>
            <Text style={styles.heroNumber}>{minutes}</Text>
            <Text style={styles.heroUnitLabel}>min</Text>
          </View>
        </View>
        <Text style={styles.heroSubLabel}>{stats?.substanceType ?? 'Nicotine'} free</Text>
      </View>

      {/* Stats Grid */}
      <View style={styles.statsGrid}>
        <View style={styles.statCard}>
          <Text style={styles.statEmoji}>🔥</Text>
          <Text style={styles.statValue}>{stats?.currentStreakDays ?? 0}</Text>
          <Text style={styles.statLabel}>Day Streak</Text>
        </View>
        <View style={styles.statCard}>
          <Text style={styles.statEmoji}>💰</Text>
          <Text style={styles.statValue}>${((stats?.moneySavedCents ?? 0) / 100).toFixed(0)}</Text>
          <Text style={styles.statLabel}>Saved</Text>
        </View>
        <View style={styles.statCard}>
          <Text style={styles.statEmoji}>⚡</Text>
          <Text style={styles.statValue}>{stats?.cravingsBeatThisWeek ?? 0}</Text>
          <Text style={styles.statLabel}>Beaten</Text>
        </View>
        <View style={styles.statCard}>
          <Text style={styles.statEmoji}>😊</Text>
          <Text style={styles.statValue}>{stats?.avgMoodThisWeek?.toFixed(1) ?? '—'}</Text>
          <Text style={styles.statLabel}>Avg Mood</Text>
        </View>
      </View>

      {/* Quick Actions */}
      <Text style={styles.sectionTitle}>Quick Actions</Text>
      <View style={styles.actions}>
        <TouchableOpacity style={[styles.actionBtn, styles.actionCraving]} onPress={() => router.push('/modals/quick-log')}>
          <Text style={styles.actionEmoji}>⚡</Text>
          <Text style={styles.actionText}>Log Craving</Text>
        </TouchableOpacity>
        <TouchableOpacity style={[styles.actionBtn, styles.actionCoach]} onPress={() => router.push('/(tabs)/coach')}>
          <Text style={styles.actionEmoji}>💬</Text>
          <Text style={styles.actionText}>Talk to Coach</Text>
        </TouchableOpacity>
        <TouchableOpacity style={[styles.actionBtn, styles.actionCbt]} onPress={() => router.push('/cbt')}>
          <Text style={styles.actionEmoji}>🧠</Text>
          <Text style={styles.actionText}>Today's Lesson</Text>
        </TouchableOpacity>
        <TouchableOpacity style={[styles.actionBtn, styles.actionJournal]} onPress={() => router.push('/journal/new')}>
          <Text style={styles.actionEmoji}>📓</Text>
          <Text style={styles.actionText}>Journal</Text>
        </TouchableOpacity>
      </View>
    </ScrollView>
  )
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#f9fafb' },
  header: { paddingHorizontal: 20, paddingTop: 60, paddingBottom: 16 },
  logo: { fontSize: 22, fontWeight: 'bold', color: '#16a34a' },
  heroCard: { margin: 16, backgroundColor: '#16a34a', borderRadius: 20, padding: 24, alignItems: 'center' },
  heroLabel: { color: '#bbf7d0', fontSize: 14, fontWeight: '500', marginBottom: 12 },
  heroTime: { flexDirection: 'row', alignItems: 'center', gap: 8 },
  heroUnit: { alignItems: 'center' },
  heroNumber: { fontSize: 48, fontWeight: 'bold', color: 'white', lineHeight: 56 },
  heroUnitLabel: { fontSize: 12, color: '#bbf7d0', marginTop: 2 },
  heroDivider: { fontSize: 36, color: '#bbf7d0', fontWeight: 'bold', marginBottom: 16 },
  heroSubLabel: { color: '#bbf7d0', fontSize: 14, marginTop: 12 },
  statsGrid: { flexDirection: 'row', flexWrap: 'wrap', paddingHorizontal: 8, gap: 8, marginBottom: 8 },
  statCard: { flex: 1, minWidth: '45%', backgroundColor: 'white', borderRadius: 16, padding: 16, alignItems: 'center', margin: 4 },
  statEmoji: { fontSize: 24, marginBottom: 4 },
  statValue: { fontSize: 24, fontWeight: 'bold', color: '#111827' },
  statLabel: { fontSize: 12, color: '#6b7280', marginTop: 2 },
  sectionTitle: { fontSize: 18, fontWeight: '600', color: '#111827', paddingHorizontal: 20, marginTop: 8, marginBottom: 12 },
  actions: { flexDirection: 'row', flexWrap: 'wrap', paddingHorizontal: 8, gap: 8, paddingBottom: 32 },
  actionBtn: { flex: 1, minWidth: '45%', borderRadius: 16, padding: 20, alignItems: 'center', margin: 4 },
  actionCraving: { backgroundColor: '#fee2e2' },
  actionCoach: { backgroundColor: '#dbeafe' },
  actionCbt: { backgroundColor: '#fef3c7' },
  actionJournal: { backgroundColor: '#f3e8ff' },
  actionEmoji: { fontSize: 28, marginBottom: 8 },
  actionText: { fontSize: 13, fontWeight: '600', color: '#374151', textAlign: 'center' },
})
