import { View, Text, StyleSheet, ScrollView, TouchableOpacity, Alert } from 'react-native'
import { useAuth, useUser } from '@clerk/clerk-expo'
import { useRouter } from 'expo-router'

export default function ProfileScreen() {
  const { signOut } = useAuth()
  const { user } = useUser()
  const router = useRouter()

  const handleSignOut = async () => {
    Alert.alert('Sign Out', 'Are you sure you want to sign out?', [
      { text: 'Cancel', style: 'cancel' },
      {
        text: 'Sign Out',
        style: 'destructive',
        onPress: async () => {
          await signOut()
          router.replace('/(auth)/sign-in')
        }
      },
    ])
  }

  return (
    <ScrollView style={styles.container} contentContainerStyle={styles.content}>
      <Text style={styles.pageTitle}>Profile</Text>

      <View style={styles.card}>
        <View style={styles.avatar}>
          <Text style={styles.avatarText}>{user?.firstName?.[0] ?? '?'}</Text>
        </View>
        <Text style={styles.name}>{user?.fullName ?? 'User'}</Text>
        <Text style={styles.email}>{user?.primaryEmailAddress?.emailAddress}</Text>
      </View>

      <View style={styles.section}>
        <Text style={styles.sectionTitle}>Subscription</Text>
        <View style={styles.planRow}>
          <Text style={styles.planName}>Free Plan</Text>
          <TouchableOpacity style={styles.upgradeBtn} onPress={() => router.push('/premium/paywall')}>
            <Text style={styles.upgradeBtnText}>Upgrade</Text>
          </TouchableOpacity>
        </View>
      </View>

      <View style={styles.section}>
        <Text style={styles.sectionTitle}>Navigation</Text>
        {[
          { label: '🏆 Badges', onPress: () => {} },
          { label: '📓 Journal', onPress: () => router.push('/journal') },
          { label: '🧠 CBT Program', onPress: () => router.push('/cbt') },
        ].map((item) => (
          <TouchableOpacity key={item.label} style={styles.menuItem} onPress={item.onPress}>
            <Text style={styles.menuItemText}>{item.label}</Text>
            <Text style={styles.menuItemArrow}>›</Text>
          </TouchableOpacity>
        ))}
      </View>

      <TouchableOpacity style={styles.signOutBtn} onPress={handleSignOut}>
        <Text style={styles.signOutText}>Sign Out</Text>
      </TouchableOpacity>
    </ScrollView>
  )
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#f9fafb' },
  content: { padding: 20, paddingTop: 60, paddingBottom: 40 },
  pageTitle: { fontSize: 28, fontWeight: 'bold', color: '#111827', marginBottom: 20 },
  card: { backgroundColor: 'white', borderRadius: 20, padding: 24, alignItems: 'center', marginBottom: 20 },
  avatar: { width: 72, height: 72, borderRadius: 36, backgroundColor: '#dcfce7', alignItems: 'center', justifyContent: 'center', marginBottom: 12 },
  avatarText: { fontSize: 28, fontWeight: 'bold', color: '#16a34a' },
  name: { fontSize: 20, fontWeight: 'bold', color: '#111827' },
  email: { fontSize: 14, color: '#6b7280', marginTop: 4 },
  section: { backgroundColor: 'white', borderRadius: 16, padding: 16, marginBottom: 16 },
  sectionTitle: { fontSize: 14, fontWeight: '600', color: '#6b7280', marginBottom: 12, textTransform: 'uppercase', letterSpacing: 0.5 },
  planRow: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between' },
  planName: { fontSize: 16, fontWeight: '600', color: '#111827' },
  upgradeBtn: { backgroundColor: '#16a34a', borderRadius: 8, paddingHorizontal: 14, paddingVertical: 8 },
  upgradeBtnText: { color: 'white', fontSize: 13, fontWeight: '600' },
  menuItem: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', paddingVertical: 14, borderBottomWidth: 1, borderBottomColor: '#f9fafb' },
  menuItemText: { fontSize: 16, color: '#111827' },
  menuItemArrow: { fontSize: 20, color: '#9ca3af' },
  signOutBtn: { borderWidth: 2, borderColor: '#fee2e2', borderRadius: 12, padding: 16, alignItems: 'center' },
  signOutText: { color: '#dc2626', fontSize: 16, fontWeight: '600' },
})
