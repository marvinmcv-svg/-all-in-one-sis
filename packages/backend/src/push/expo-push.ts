import Expo, { ExpoPushMessage, ExpoPushTicket } from 'expo-server-sdk'

const expo = new Expo({ accessToken: process.env['EXPO_ACCESS_TOKEN'] })

export interface PushPayload {
  token: string
  title: string
  body: string
  data?: Record<string, string>
}

export async function sendPushNotification(payload: PushPayload): Promise<void> {
  if (!Expo.isExpoPushToken(payload.token)) {
    console.warn(`Invalid Expo push token: ${payload.token}`)
    return
  }

  const message: ExpoPushMessage = {
    to: payload.token,
    sound: 'default',
    title: payload.title,
    body: payload.body,
    data: payload.data ?? {},
  }

  const chunks = expo.chunkPushNotifications([message])

  for (const chunk of chunks) {
    try {
      const tickets: ExpoPushTicket[] = await expo.sendPushNotificationsAsync(chunk)
      for (const ticket of tickets) {
        if (ticket.status === 'error') {
          console.error('Push notification error:', ticket.message)
          if (ticket.details?.error === 'DeviceNotRegistered') {
            // Token is invalid — should remove it from DB
            console.warn('Device not registered, token should be removed:', payload.token)
          }
        }
      }
    } catch (err) {
      console.error('Failed to send push chunk:', err)
    }
  }
}

export async function sendBulkPushNotifications(payloads: PushPayload[]): Promise<void> {
  const valid = payloads.filter((p) => Expo.isExpoPushToken(p.token))
  if (valid.length === 0) return

  const messages: ExpoPushMessage[] = valid.map((p) => ({
    to: p.token,
    sound: 'default' as const,
    title: p.title,
    body: p.body,
    data: p.data ?? {},
  }))

  const chunks = expo.chunkPushNotifications(messages)
  for (const chunk of chunks) {
    try {
      await expo.sendPushNotificationsAsync(chunk)
    } catch (err) {
      console.error('Failed to send push chunk:', err)
    }
  }
}
