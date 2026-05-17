import * as Notifications from 'expo-notifications'
import * as Device from 'expo-device'
import { Platform } from 'react-native'

// Configure how notifications appear when app is in foreground
Notifications.setNotificationHandler({
  handleNotification: async () => ({
    shouldShowAlert: true,
    shouldPlaySound: true,
    shouldSetBadge: false,
  }),
})

export async function registerForPushNotifications(apiUrl: string, token: string): Promise<string | null> {
  if (!Device.isDevice) return null  // simulator/emulator — skip

  if (Platform.OS === 'android') {
    await Notifications.setNotificationChannelAsync('default', {
      name: 'Default',
      importance: Notifications.AndroidImportance.MAX,
      vibrationPattern: [0, 250, 250, 250],
    })
  }

  const { status: existingStatus } = await Notifications.getPermissionsAsync()
  let finalStatus = existingStatus

  if (existingStatus !== 'granted') {
    const { status } = await Notifications.requestPermissionsAsync()
    finalStatus = status
  }

  if (finalStatus !== 'granted') return null

  const pushToken = (await Notifications.getExpoPushTokenAsync()).data

  // Save to backend
  try {
    await fetch(`${apiUrl}/api/v1/users/push-token`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
      body: JSON.stringify({ token: pushToken }),
    })
  } catch {
    // Non-fatal — will retry next launch
  }

  return pushToken
}

// Map notification data.screen to expo-router paths
export function getRouteFromNotificationData(data: Record<string, string>): string {
  const screenMap: Record<string, string> = {
    'quick-log': '/modals/quick-log',
    'track': '/(tabs)/track',
    'cbt': '/cbt',
    'badges': '/(tabs)/profile',
    'dashboard': '/(tabs)/home',
    'community': '/(tabs)/community',
  }
  return screenMap[data['screen'] ?? ''] ?? '/(tabs)/home'
}
