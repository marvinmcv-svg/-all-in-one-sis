import { View, Text, StyleSheet, ScrollView } from 'react-native';

interface AttendanceRecord {
  date: string;
  course: string;
  status: 'present' | 'absent' | 'late' | 'excused';
}

interface WeeklyStats {
  present: number;
  absent: number;
  late: number;
  excused: number;
}

const mockWeeklyStats: WeeklyStats = {
  present: 18,
  absent: 1,
  late: 1,
  excused: 0,
};

const mockAttendance: AttendanceRecord[] = [
  { date: 'May 5, 2026', course: 'CS 301', status: 'present' },
  { date: 'May 5, 2026', course: 'MATH 202', status: 'present' },
  { date: 'May 4, 2026', course: 'ENG 101', status: 'late' },
  { date: 'May 4, 2026', course: 'PHYS 201', status: 'present' },
  { date: 'May 4, 2026', course: 'CS 450', status: 'present' },
  { date: 'May 3, 2026', course: 'CS 301', status: 'absent' },
  { date: 'May 3, 2026', course: 'MATH 202', status: 'excused' },
];

const getStatusStyle = (status: AttendanceRecord['status']) => {
  switch (status) {
    case 'present':
      return { bg: '#D1FAE5', text: '#059669', label: 'Present' };
    case 'absent':
      return { bg: '#FEE2E2', text: '#DC2626', label: 'Absent' };
    case 'late':
      return { bg: '#FEF3C7', text: '#D97706', label: 'Late' };
    case 'excused':
      return { bg: '#E0E7FF', text: '#4F46E5', label: 'Excused' };
  }
};

export default function AttendanceScreen() {
  const totalClasses = mockWeeklyStats.present + mockWeeklyStats.absent + mockWeeklyStats.late + mockWeeklyStats.excused;
  const attendanceRate = ((mockWeeklyStats.present / totalClasses) * 100).toFixed(1);

  return (
    <ScrollView style={styles.container} contentContainerStyle={styles.content}>
      <View style={styles.overviewCard}>
        <Text style={styles.overviewTitle}>Attendance Overview</Text>
        <View style={styles.overviewStats}>
          <View style={styles.mainStat}>
            <Text style={styles.mainStatValue}>{attendanceRate}%</Text>
            <Text style={styles.mainStatLabel}>Attendance Rate</Text>
          </View>
          <View style={styles.divider} />
          <View style={styles.secondaryStats}>
            <View style={styles.statRow}>
              <View style={[styles.dot, { backgroundColor: '#10B981' }]} />
              <Text style={styles.statText}>Present: {mockWeeklyStats.present}</Text>
            </View>
            <View style={styles.statRow}>
              <View style={[styles.dot, { backgroundColor: '#EF4444' }]} />
              <Text style={styles.statText}>Absent: {mockWeeklyStats.absent}</Text>
            </View>
            <View style={styles.statRow}>
              <View style={[styles.dot, { backgroundColor: '#F59E0B' }]} />
              <Text style={styles.statText}>Late: {mockWeeklyStats.late}</Text>
            </View>
            <View style={styles.statRow}>
              <View style={[styles.dot, { backgroundColor: '#6366F1' }]} />
              <Text style={styles.statText}>Excused: {mockWeeklyStats.excused}</Text>
            </View>
          </View>
        </View>
      </View>

      <Text style={styles.sectionTitle}>Recent Attendance</Text>

      <View style={styles.attendanceList}>
        {mockAttendance.map((record, index) => {
          const statusStyle = getStatusStyle(record.status);
          return (
            <View key={index} style={styles.attendanceRow}>
              <View style={styles.dateCourse}>
                <Text style={styles.courseText}>{record.course}</Text>
                <Text style={styles.dateText}>{record.date}</Text>
              </View>
              <View style={[styles.statusBadge, { backgroundColor: statusStyle.bg }]}>
                <Text style={[styles.statusText, { color: statusStyle.text }]}>
                  {statusStyle.label}
                </Text>
              </View>
            </View>
          );
        })}
      </View>
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
  overviewCard: {
    backgroundColor: '#FFFFFF',
    borderRadius: 16,
    padding: 20,
    marginBottom: 24,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.06,
    shadowRadius: 4,
    elevation: 2,
  },
  overviewTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: '#111827',
    marginBottom: 16,
  },
  overviewStats: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  mainStat: {
    flex: 1,
    alignItems: 'center',
  },
  mainStatValue: {
    fontSize: 36,
    fontWeight: '700',
    color: '#10B981',
  },
  mainStatLabel: {
    fontSize: 14,
    color: '#6B7280',
    marginTop: 4,
  },
  divider: {
    width: 1,
    height: 60,
    backgroundColor: '#E5E7EB',
    marginHorizontal: 16,
  },
  secondaryStats: {
    flex: 1,
    gap: 8,
  },
  statRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  dot: {
    width: 10,
    height: 10,
    borderRadius: 5,
  },
  statText: {
    fontSize: 14,
    color: '#6B7280',
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: '#111827',
    marginBottom: 12,
  },
  attendanceList: {
    backgroundColor: '#FFFFFF',
    borderRadius: 16,
    overflow: 'hidden',
  },
  attendanceRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: 16,
    borderBottomWidth: 1,
    borderBottomColor: '#F3F4F6',
  },
  dateCourse: {},
  courseText: {
    fontSize: 16,
    fontWeight: '500',
    color: '#111827',
  },
  dateText: {
    fontSize: 12,
    color: '#9CA3AF',
    marginTop: 2,
  },
  statusBadge: {
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 8,
  },
  statusText: {
    fontSize: 12,
    fontWeight: '600',
  },
});
