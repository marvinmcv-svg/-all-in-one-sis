import { Tabs } from 'expo-router';
import { View, Text, StyleSheet } from 'react-native';

type TabIconProps = {
  name: string;
  focused: boolean;
};

function TabIcon({ name, focused }: TabIconProps) {
  const icons: Record<string, string> = {
    Home: '🏠',
    Courses: '📚',
    Attendance: '📅',
    Grades: '📊',
    Messages: '💬',
  };

  return (
    <View style={styles.iconContainer}>
      <Text style={[styles.icon, focused && styles.iconFocused]}>
        {icons[name] ?? '•'}
      </Text>
    </View>
  );
}

export default function TabLayout() {
  return (
    <Tabs
      screenOptions={{
        tabBarActiveTintColor: '#3B82F6',
        tabBarInactiveTintColor: '#9CA3AF',
        tabBarStyle: {
          backgroundColor: '#FFFFFF',
          borderTopColor: '#E5E7EB',
          height: 60,
          paddingBottom: 8,
          paddingTop: 8,
        },
        tabBarLabelStyle: {
          fontSize: 12,
          fontWeight: '500',
        },
        headerStyle: {
          backgroundColor: '#3B82F6',
        },
        headerTintColor: '#FFFFFF',
        headerTitleStyle: {
          fontWeight: '600',
        },
      }}
    >
      <Tabs.Screen
        name="index"
        options={{
          title: 'Home',
          headerTitle: 'Dashboard',
          tabBarIcon: ({ focused }) => <TabIcon name="Home" focused={focused} />,
        }}
      />
      <Tabs.Screen
        name="courses"
        options={{
          title: 'Courses',
          headerTitle: 'My Courses',
          tabBarIcon: ({ focused }) => <TabIcon name="Courses" focused={focused} />,
        }}
      />
      <Tabs.Screen
        name="attendance"
        options={{
          title: 'Attendance',
          headerTitle: 'Attendance',
          tabBarIcon: ({ focused }) => <TabIcon name="Attendance" focused={focused} />,
        }}
      />
      <Tabs.Screen
        name="grades"
        options={{
          title: 'Grades',
          headerTitle: 'My Grades',
          tabBarIcon: ({ focused }) => <TabIcon name="Grades" focused={focused} />,
        }}
      />
      <Tabs.Screen
        name="messages"
        options={{
          title: 'Messages',
          headerTitle: 'My Messages',
          tabBarIcon: ({ focused }) => <TabIcon name="Messages" focused={focused} />,
        }}
      />
    </Tabs>
  );
}

const styles = StyleSheet.create({
  iconContainer: {
    alignItems: 'center',
    justifyContent: 'center',
  },
  icon: {
    fontSize: 20,
    opacity: 0.6,
  },
  iconFocused: {
    opacity: 1,
  },
});
