import { Stack } from 'expo-router';
import { StatusBar } from 'expo-status-bar';
import { useAuthStore } from '@/lib/auth';
import { useEffect } from 'react';

export default function RootLayout() {
  const { token } = useAuthStore();

  useEffect(() => {
    // Set auth token for API client when it changes
    if (token) {
      import('@/lib/api').then(({ apiClient }) => {
        apiClient.setToken(token);
      });
    }
  }, [token]);

  return (
    <>
      <StatusBar style="auto" />
      <Stack
        screenOptions={{
          headerShown: false,
        }}
      >
        <Stack.Screen name="index" />
        <Stack.Screen
          name="(tabs)"
          options={{
            headerShown: false,
          }}
        />
      </Stack>
    </>
  );
}
