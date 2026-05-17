import { ClerkProvider, useAuth } from '@clerk/clerk-expo'
import * as SecureStore from 'expo-secure-store'
import { GestureHandlerRootView } from 'react-native-gesture-handler'
import { Slot, useRouter, useSegments } from 'expo-router'
import { useEffect, useRef } from 'react'
import { StyleSheet } from 'react-native'
import * as Notifications from 'expo-notifications'
import { registerForPushNotifications, getRouteFromNotificationData } from '../lib/notifications'

const tokenCache = {
  async getToken(key: string) {
    return SecureStore.getItemAsync(key)
  },
  async saveToken(key: string, value: string) {
    return SecureStore.setItemAsync(key, value)
  },
}

function AuthGuard() {
  const { isLoaded, isSignedIn, getToken } = useAuth()
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

  const notificationListener = useRef<Notifications.Subscription | null>(null)
  const responseListener = useRef<Notifications.Subscription | null>(null)

  useEffect(() => {
    if (!isSignedIn) return

    // Register for push notifications
    void getToken().then((token) => {
      if (token) {
        void registerForPushNotifications(process.env['EXPO_PUBLIC_API_URL'] ?? '', token)
      }
    })

    // Handle notification tap when app is open
    notificationListener.current = Notifications.addNotificationReceivedListener(() => {
      // notification received while app is open — no action needed
    })

    // Handle notification tap → navigate to screen
    responseListener.current = Notifications.addNotificationResponseReceivedListener((response) => {
      const data = response.notification.request.content.data as Record<string, string>
      const route = getRouteFromNotificationData(data)
      router.push(route as never)
    })

    return () => {
      notificationListener.current?.remove()
      responseListener.current?.remove()
    }
  }, [isSignedIn])

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
