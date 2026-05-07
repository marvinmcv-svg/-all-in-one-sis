import { View, Text, FlatList, StyleSheet, TouchableOpacity } from 'react-native';

interface Course {
  id: string;
  code: string;
  name: string;
  instructor: string;
  credits: number;
  schedule: string;
  progress: number;
}

const mockCourses: Course[] = [
  {
    id: '1',
    code: 'CS 301',
    name: 'Data Structures & Algorithms',
    instructor: 'Dr. Smith',
    credits: 4,
    schedule: 'Mon/Wed 10:00 AM',
    progress: 68,
  },
  {
    id: '2',
    code: 'MATH 202',
    name: 'Linear Algebra',
    instructor: 'Prof. Johnson',
    credits: 3,
    schedule: 'Tue/Thu 2:00 PM',
    progress: 45,
  },
  {
    id: '3',
    code: 'ENG 101',
    name: 'Technical Writing',
    instructor: 'Ms. Davis',
    credits: 3,
    schedule: 'Fri 9:00 AM',
    progress: 82,
  },
  {
    id: '4',
    code: 'PHYS 201',
    name: 'Electricity & Magnetism',
    instructor: 'Dr. Brown',
    credits: 4,
    schedule: 'Mon/Wed/Fri 11:00 AM',
    progress: 55,
  },
  {
    id: '5',
    code: 'CS 450',
    name: 'Database Systems',
    instructor: 'Prof. Wilson',
    credits: 3,
    schedule: 'Tue/Thu 4:00 PM',
    progress: 30,
  },
];

export default function CoursesScreen() {
  const renderCourse = ({ item }: { item: Course }) => (
    <TouchableOpacity style={styles.courseCard}>
      <View style={styles.courseHeader}>
        <View style={styles.courseCodeContainer}>
          <Text style={styles.courseCode}>{item.code}</Text>
          <Text style={styles.credits}>{item.credits} credits</Text>
        </View>
        <View style={styles.progressContainer}>
          <Text style={styles.progressText}>{item.progress}%</Text>
          <View style={styles.progressBar}>
            <View
              style={[styles.progressFill, { width: `${item.progress}%` }]}
            />
          </View>
        </View>
      </View>

      <Text style={styles.courseName}>{item.name}</Text>

      <View style={styles.courseDetails}>
        <View style={styles.detailRow}>
          <Text style={styles.detailIcon}>👤</Text>
          <Text style={styles.detailText}>{item.instructor}</Text>
        </View>
        <View style={styles.detailRow}>
          <Text style={styles.detailIcon}>🕐</Text>
          <Text style={styles.detailText}>{item.schedule}</Text>
        </View>
      </View>
    </TouchableOpacity>
  );

  return (
    <View style={styles.container}>
      <FlatList
        data={mockCourses}
        renderItem={renderCourse}
        keyExtractor={(item) => item.id}
        contentContainerStyle={styles.list}
        showsVerticalScrollIndicator={false}
      />
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#F9FAFB',
  },
  list: {
    padding: 16,
    gap: 12,
  },
  courseCard: {
    backgroundColor: '#FFFFFF',
    borderRadius: 16,
    padding: 16,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.06,
    shadowRadius: 4,
    elevation: 2,
  },
  courseHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
    marginBottom: 12,
  },
  courseCodeContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  courseCode: {
    fontSize: 18,
    fontWeight: '700',
    color: '#3B82F6',
  },
  credits: {
    fontSize: 12,
    color: '#9CA3AF',
    backgroundColor: '#F3F4F6',
    paddingHorizontal: 8,
    paddingVertical: 2,
    borderRadius: 4,
  },
  progressContainer: {
    alignItems: 'flex-end',
  },
  progressText: {
    fontSize: 14,
    fontWeight: '600',
    color: '#10B981',
    marginBottom: 4,
  },
  progressBar: {
    width: 80,
    height: 6,
    backgroundColor: '#E5E7EB',
    borderRadius: 3,
    overflow: 'hidden',
  },
  progressFill: {
    height: '100%',
    backgroundColor: '#10B981',
    borderRadius: 3,
  },
  courseName: {
    fontSize: 16,
    fontWeight: '600',
    color: '#111827',
    marginBottom: 12,
  },
  courseDetails: {
    gap: 6,
  },
  detailRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  detailIcon: {
    fontSize: 14,
  },
  detailText: {
    fontSize: 14,
    color: '#6B7280',
  },
});
