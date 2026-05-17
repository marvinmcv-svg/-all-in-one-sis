import { ClerkProvider, useAuth } from '@clerk/clerk-expo'
import * as SecureStore from 'expo-secure-store'
import { GestureHandlerRootView } from 'react-native-gesture-handler'
import { Slot, useRouter, useSegments } from 'expo-router'
import { useEffect } from 'react'
import { StyleSheet } from 'react-native'

const tokenCache = {
  async getToken(key: string) {
    return SecureStore.getItemAsync(key)
  },
  async saveToken(key: string, value: string) {
    return SecureStore.setItemAsync(key, value)
  },
}

function AuthGuard() {
  const { isLoaded, isSignedIn } = useAuth()
  const segments = useSegments()
  const router = useRouter()

  useEffect(() => {
    if (!isLoaded) return
    const inAuthGroup = segments[0] === '(auth)'
    if (!isSignedIn && !inAuthGroup) {
      router.replace('/(auth)/sign-in')
    } else if (isSignedIn && inAuthGroup) {
      router.replace('/(tabs)/home')
    }
  }, [isLoaded, isSignedIn, segments])

  return <Slot />
}

export default function RootLayout() {
  return (
    <ClerkProvider
      tokenCache={tokenCache}
      publishableKey={process.env.EXPO_PUBLIC_CLERK_PUBLISHABLE_KEY!}
    >
      <GestureHandlerRootView style={styles.root}>
        <AuthGuard />
      </GestureHandlerRootView>
    </ClerkProvider>
  )
}

const styles = StyleSheet.create({
  root: { flex: 1 },
})
