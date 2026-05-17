import { Tabs } from 'expo-router'

export default function TabsLayout() {
  return (
    <Tabs
      screenOptions={{
        tabBarActiveTintColor: '#16a34a',
        tabBarInactiveTintColor: '#9ca3af',
        tabBarStyle: { borderTopColor: '#f3f4f6' },
        headerShown: false,
      }}
    >
      <Tabs.Screen name="home" options={{ title: 'Home', tabBarIcon: ({ color }) => <TabIcon emoji="🏠" color={color} /> }} />
      <Tabs.Screen name="track" options={{ title: 'Track', tabBarIcon: ({ color }) => <TabIcon emoji="📊" color={color} /> }} />
      <Tabs.Screen name="coach" options={{ title: 'AI Coach', tabBarIcon: ({ color }) => <TabIcon emoji="💬" color={color} /> }} />
      <Tabs.Screen name="community" options={{ title: 'Community', tabBarIcon: ({ color }) => <TabIcon emoji="🤝" color={color} /> }} />
      <Tabs.Screen name="profile" options={{ title: 'Profile', tabBarIcon: ({ color }) => <TabIcon emoji="👤" color={color} /> }} />
    </Tabs>
  )
}

function TabIcon({ emoji, color }: { emoji: string; color: string }) {
  const { Text } = require('react-native')
  return <Text style={{ fontSize: 20, opacity: color === '#16a34a' ? 1 : 0.5 }}>{emoji}</Text>
}
