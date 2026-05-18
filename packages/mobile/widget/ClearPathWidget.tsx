/**
 * ClearPath Home Screen Widget
 *
 * Native widget implementation requires one of:
 *   iOS: expo-widgets (community) or EAS Build + WidgetKit native target
 *   Android: react-native-android-widget or EAS Build + Glance target
 *
 * This file defines the widget UI logic and data contract.
 * Wire it to the native layer via the eas.json "plugins" array once the
 * native module is installed.
 *
 * Widget displays:
 *   - Days + hours clean (updated each render)
 *   - Current streak flame indicator
 *   - "Log Craving" tap → opens clearpath://quick-log
 *   - "Beat It 💪" tap → logs craving as beaten silently (background fetch)
 */

export interface WidgetData {
  daysClean: number
  hoursClean: number
  streakDays: number
  lastUpdated: string
}

export function computeWidgetData(quitDateISO: string): WidgetData {
  const quitDate = new Date(quitDateISO)
  const secondsClean = Math.floor((Date.now() - quitDate.getTime()) / 1000)
  const daysClean = Math.floor(secondsClean / 86400)
  const hoursClean = Math.floor((secondsClean % 86400) / 3600)

  return {
    daysClean,
    hoursClean,
    streakDays: daysClean,
    lastUpdated: new Date().toISOString(),
  }
}

export async function fetchAndCacheWidgetData(
  apiUrl: string,
  token: string,
): Promise<WidgetData | null> {
  try {
    const res = await fetch(`${apiUrl}/api/v1/dashboard/stats`, {
      headers: { Authorization: `Bearer ${token}` },
    })
    const json = await res.json() as {
      success: boolean
      data: { daysClean: number; currentStreakDays: number; cleanSinceDatetime: string }
    }
    if (!json.success) return null

    const secondsClean = Math.floor(
      (Date.now() - new Date(json.data.cleanSinceDatetime).getTime()) / 1000,
    )

    return {
      daysClean: json.data.daysClean,
      hoursClean: Math.floor((secondsClean % 86400) / 3600),
      streakDays: json.data.currentStreakDays,
      lastUpdated: new Date().toISOString(),
    }
  } catch {
    return null
  }
}

// Deep link targets (handled by expo-router in _layout.tsx)
export const WIDGET_DEEP_LINKS = {
  quickLog: 'clearpath://modals/quick-log',
  beatIt: 'clearpath://beat-it',   // background action URL scheme
  home: 'clearpath://(tabs)/home',
} as const
