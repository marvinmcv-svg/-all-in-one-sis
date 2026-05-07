import { View, Text, ScrollView, StyleSheet, TouchableOpacity } from 'react-native';
import { useAuthStore } from '@/lib/auth';
import { useRouter } from 'expo-router';

interface QuickStat {
  label: string;
  value: string;
  color: string;
}

interface Notice {
  id: string;
  title: string;
  date: string;
  priority: 'high' | 'normal';
}

export default function HomeScreen() {
  const { user, logout } = useAuthStore();
  const router = useRouter();

  const quickStats: QuickStat[] = [
    { label: 'GPA', value: '3.75', color: '#3B82F6' },
    { label: 'Attendance', value: '94%', color: '#10B981' },
    { label: 'Courses', value: '5', color: '#8B5CF6' },
    { label: 'Credits', value: '18', color: '#F59E0B' },
  ];

  const notices: Notice[] = [
    { id: '1', title: 'Mid-term exams start next week', date: 'May 12', priority: 'high' },
    { id: '2', title: 'Course registration opens May 20', date: 'May 10', priority: 'normal' },
    { id: '3', title: 'New library resources available', date: 'May 8', priority: 'normal' },
  ];

  const handleLogout = () => {
    logout();
    router.replace('/');
  };

  return (
    <ScrollView style={styles.container} contentContainerStyle={styles.content}>
      <View style={styles.welcomeSection}>
        <Text style={styles.welcomeText}>Welcome back,</Text>
        <Text style={styles.userName}>{user?.name ?? 'Student'}</Text>
        <Text style={styles.studentId}>{user?.studentId ?? ''}</Text>
      </View>

      <View style={styles.statsGrid}>
        {quickStats.map((stat) => (
          <View key={stat.label} style={styles.statCard}>
            <Text style={[styles.statValue, { color: stat.color }]}>{stat.value}</Text>
            <Text style={styles.statLabel}>{stat.label}</Text>
          </View>
        ))}
      </View>

      <View style={styles.section}>
        <Text style={styles.sectionTitle}>Quick Actions</Text>
        <View style={styles.actionsRow}>
          <TouchableOpacity style={styles.actionButton}>
            <Text style={styles.actionIcon}>📋</Text>
            <Text style={styles.actionLabel}>Schedule</Text>
          </TouchableOpacity>
          <TouchableOpacity style={styles.actionButton}>
            <Text style={styles.actionIcon}>📝</Text>
            <Text style={styles.actionLabel}>Assignments</Text>
          </TouchableOpacity>
          <TouchableOpacity style={styles.actionButton}>
            <Text style={styles.actionIcon}>💬</Text>
            <Text style={styles.actionLabel}>Messages</Text>
          </TouchableOpacity>
          <TouchableOpacity style={styles.actionButton}>
            <Text style={styles.actionIcon}>📞</Text>
            <Text style={styles.actionLabel}>Support</Text>
          </TouchableOpacity>
        </View>
      </View>

      <View style={styles.section}>
        <Text style={styles.sectionTitle}>Announcements</Text>
        {notices.map((notice) => (
          <View
            key={notice.id}
            style={[
              styles.noticeCard,
              notice.priority === 'high' && styles.noticeHighPriority,
            ]}
          >
            <View style={styles.noticeContent}>
              <Text style={styles.noticeTitle}>{notice.title}</Text>
              <Text style={styles.noticeDate}>{notice.date}</Text>
            </View>
            {notice.priority === 'high' && (
              <View style={styles.priorityBadge}>
                <Text style={styles.priorityText}>NEW</Text>
              </View>
            )}
          </View>
        ))}
      </View>

      <TouchableOpacity style={styles.logoutButton} onPress={handleLogout}>
        <Text style={styles.logoutText}>Sign Out</Text>
      </TouchableOpacity>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#F9FAFB',
  },
  content: {
    padding: 16,
    paddingBottom: 32,
  },
  welcomeSection: {
    backgroundColor: '#3B82F6',
    borderRadius: 16,
    padding: 20,
    marginBottom: 20,
  },
  welcomeText: {
    fontSize: 14,
    color: '#BFDBFE',
  },
  userName: {
    fontSize: 24,
    fontWeight: '700',
    color: '#FFFFFF',
    marginTop: 4,
  },
  studentId: {
    fontSize: 14,
    color: '#93C5FD',
    marginTop: 4,
  },
  statsGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 12,
    marginBottom: 24,
  },
  statCard: {
    flex: 1,
    minWidth: '45%',
    backgroundColor: '#FFFFFF',
    borderRadius: 12,
    padding: 16,
    alignItems: 'center',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.05,
    shadowRadius: 2,
    elevation: 1,
  },
  statValue: {
    fontSize: 28,
    fontWeight: '700',
  },
  statLabel: {
    fontSize: 14,
    color: '#6B7280',
    marginTop: 4,
  },
  section: {
    marginBottom: 24,
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: '#111827',
    marginBottom: 12,
  },
  actionsRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
  },
  actionButton: {
    flex: 1,
    backgroundColor: '#FFFFFF',
    borderRadius: 12,
    padding: 16,
    alignItems: 'center',
    marginHorizontal: 4,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.05,
    shadowRadius: 2,
    elevation: 1,
  },
  actionIcon: {
    fontSize: 24,
    marginBottom: 8,
  },
  actionLabel: {
    fontSize: 12,
    color: '#6B7280',
    fontWeight: '500',
  },
  noticeCard: {
    backgroundColor: '#FFFFFF',
    borderRadius: 12,
    padding: 16,
    marginBottom: 8,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.05,
    shadowRadius: 2,
    elevation: 1,
  },
  noticeHighPriority: {
    borderLeftWidth: 4,
    borderLeftColor: '#EF4444',
  },
  noticeContent: {
    flex: 1,
  },
  noticeTitle: {
    fontSize: 14,
    fontWeight: '500',
    color: '#111827',
  },
  noticeDate: {
    fontSize: 12,
    color: '#9CA3AF',
    marginTop: 4,
  },
  priorityBadge: {
    backgroundColor: '#FEE2E2',
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 4,
  },
  priorityText: {
    fontSize: 10,
    fontWeight: '700',
    color: '#EF4444',
  },
  logoutButton: {
    backgroundColor: '#FEE2E2',
    borderRadius: 12,
    paddingVertical: 14,
    alignItems: 'center',
    marginTop: 8,
  },
  logoutText: {
    fontSize: 16,
    fontWeight: '600',
    color: '#EF4444',
  },
});
