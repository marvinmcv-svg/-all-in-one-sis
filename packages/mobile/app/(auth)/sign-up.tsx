import { useSignUp } from '@clerk/clerk-expo'
import { View, Text, TextInput, TouchableOpacity, StyleSheet, Alert } from 'react-native'
import { useState } from 'react'
import { useRouter } from 'expo-router'

export default function SignUpScreen() {
  const { signUp, setActive, isLoaded } = useSignUp()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [loading, setLoading] = useState(false)
  const router = useRouter()

  const handleSignUp = async () => {
    if (!isLoaded) return
    setLoading(true)
    try {
      const result = await signUp.create({ emailAddress: email, password })
      if (result.status === 'complete') {
        await setActive({ session: result.createdSessionId })
        router.replace('/onboarding')
      }
    } catch (err) {
      Alert.alert('Error', 'Could not create account. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <View style={styles.container}>
      <View style={styles.header}>
        <Text style={styles.logo}>🌱 ClearPath</Text>
        <Text style={styles.tagline}>The first dual-substance recovery platform</Text>
      </View>

      <View style={styles.form}>
        <Text style={styles.title}>Create your account</Text>
        <TextInput
          style={styles.input}
          placeholder="Email"
          value={email}
          onChangeText={setEmail}
          keyboardType="email-address"
          autoCapitalize="none"
        />
        <TextInput
          style={styles.input}
          placeholder="Password"
          value={password}
          onChangeText={setPassword}
          secureTextEntry
        />
        <TouchableOpacity
          style={[styles.button, loading && styles.buttonDisabled]}
          onPress={handleSignUp}
          disabled={loading}
        >
          <Text style={styles.buttonText}>{loading ? 'Creating account...' : 'Get Started Free'}</Text>
        </TouchableOpacity>

        <TouchableOpacity onPress={() => router.push('/(auth)/sign-in')} style={styles.link}>
          <Text style={styles.linkText}>Already have an account? Sign in</Text>
        </TouchableOpacity>
      </View>
    </View>
  )
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#f9fafb', padding: 24 },
  header: { alignItems: 'center', paddingTop: 80, paddingBottom: 48 },
  logo: { fontSize: 32, fontWeight: 'bold', color: '#16a34a' },
  tagline: { fontSize: 14, color: '#6b7280', marginTop: 8, textAlign: 'center' },
  form: { gap: 12 },
  title: { fontSize: 24, fontWeight: 'bold', color: '#111827', marginBottom: 8 },
  input: { borderWidth: 1, borderColor: '#d1d5db', borderRadius: 12, padding: 16, fontSize: 16, backgroundColor: 'white' },
  button: { backgroundColor: '#16a34a', borderRadius: 12, padding: 16, alignItems: 'center', marginTop: 8 },
  buttonDisabled: { opacity: 0.6 },
  buttonText: { color: 'white', fontSize: 16, fontWeight: '600' },
  link: { alignItems: 'center', marginTop: 16 },
  linkText: { color: '#16a34a', fontSize: 14 },
})
