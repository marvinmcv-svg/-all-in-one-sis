import { View, Text, StyleSheet, ScrollView } from 'react-native';

interface Grade {
  course: string;
  courseName: string;
  assignments: AssignmentGrade[];
  currentGrade: number;
  letterGrade: string;
}

interface AssignmentGrade {
  name: string;
  score: number;
  maxScore: number;
  date: string;
}

const mockGrades: Grade[] = [
  {
    course: 'CS 301',
    courseName: 'Data Structures & Algorithms',
    currentGrade: 92,
    letterGrade: 'A',
    assignments: [
      { name: 'Homework 1', score: 95, maxScore: 100, date: 'Feb 15' },
      { name: 'Quiz 1', score: 88, maxScore: 100, date: 'Feb 22' },
      { name: 'Midterm', score: 91, maxScore: 100, date: 'Mar 10' },
      { name: 'Homework 2', score: 94, maxScore: 100, date: 'Mar 18' },
    ],
  },
  {
    course: 'MATH 202',
    courseName: 'Linear Algebra',
    currentGrade: 85,
    letterGrade: 'B',
    assignments: [
      { name: 'Problem Set 1', score: 82, maxScore: 100, date: 'Feb 14' },
      { name: 'Quiz 1', score: 88, maxScore: 100, date: 'Feb 21' },
      { name: 'Midterm', score: 85, maxScore: 100, date: 'Mar 8' },
    ],
  },
  {
    course: 'ENG 101',
    courseName: 'Technical Writing',
    currentGrade: 94,
    letterGrade: 'A',
    assignments: [
      { name: 'Essay 1', score: 92, maxScore: 100, date: 'Feb 16' },
      { name: 'Lab Report', score: 96, maxScore: 100, date: 'Mar 2' },
    ],
  },
  {
    course: 'PHYS 201',
    courseName: 'Electricity & Magnetism',
    currentGrade: 78,
    letterGrade: 'C+',
    assignments: [
      { name: 'Homework 1', score: 80, maxScore: 100, date: 'Feb 17' },
      { name: 'Lab 1', score: 72, maxScore: 100, date: 'Feb 24' },
      { name: 'Midterm', score: 82, maxScore: 100, date: 'Mar 12' },
    ],
  },
  {
    course: 'CS 450',
    courseName: 'Database Systems',
    currentGrade: 88,
    letterGrade: 'B+',
    assignments: [
      { name: 'Project 1', score: 90, maxScore: 100, date: 'Feb 20' },
      { name: 'Quiz 1', score: 85, maxScore: 100, date: 'Mar 1' },
    ],
  },
];

const getGradeColor = (grade: number): string => {
  if (grade >= 90) return '#10B981';
  if (grade >= 80) return '#3B82F6';
  if (grade >= 70) return '#F59E0B';
  return '#EF4444';
};

export default function GradesScreen() {
  const gpa = (
    mockGrades.reduce((sum, g) => sum + g.currentGrade, 0) / mockGrades.length / 25
  ).toFixed(2);

  return (
    <ScrollView style={styles.container} contentContainerStyle={styles.content}>
      <View style={styles.gpaCard}>
        <Text style={styles.gpaLabel}>Current GPA</Text>
        <Text style={styles.gpaValue}>{gpa}</Text>
        <Text style={styles.gpaScale}>out of 4.0</Text>
      </View>

      <Text style={styles.sectionTitle}>Course Grades</Text>

      {mockGrades.map((grade) => (
        <View key={grade.course} style={styles.courseCard}>
          <View style={styles.courseHeader}>
            <View>
              <Text style={styles.courseCode}>{grade.course}</Text>
              <Text style={styles.courseName}>{grade.courseName}</Text>
            </View>
            <View style={styles.gradeCircle}>
              <Text
                style={[
                  styles.gradeValue,
                  { color: getGradeColor(grade.currentGrade) },
                ]}
              >
                {grade.currentGrade}
              </Text>
              <Text style={styles.letterGrade}>{grade.letterGrade}</Text>
            </View>
          </View>

          <View style={styles.assignmentsList}>
            {grade.assignments.map((assignment, index) => (
              <View key={index} style={styles.assignmentRow}>
                <View>
                  <Text style={styles.assignmentName}>{assignment.name}</Text>
                  <Text style={styles.assignmentDate}>{assignment.date}</Text>
                </View>
                <View style={styles.scoreContainer}>
                  <Text style={styles.scoreText}>
                    {assignment.score}/{assignment.maxScore}
                  </Text>
                  <View style={styles.scoreBar}>
                    <View
                      style={[
                        styles.scoreFill,
                        {
                          width: `${(assignment.score / assignment.maxScore) * 100}%`,
                          backgroundColor: getGradeColor(
                            (assignment.score / assignment.maxScore) * 100
                          ),
                        },
                      ]}
                    />
                  </View>
                </View>
              </View>
            ))}
          </View>
        </View>
      ))}
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
  gpaCard: {
    backgroundColor: '#3B82F6',
    borderRadius: 16,
    padding: 24,
    alignItems: 'center',
    marginBottom: 24,
  },
  gpaLabel: {
    fontSize: 14,
    color: '#BFDBFE',
    marginBottom: 4,
  },
  gpaValue: {
    fontSize: 56,
    fontWeight: '700',
    color: '#FFFFFF',
  },
  gpaScale: {
    fontSize: 14,
    color: '#93C5FD',
    marginTop: 4,
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: '#111827',
    marginBottom: 12,
  },
  courseCard: {
    backgroundColor: '#FFFFFF',
    borderRadius: 16,
    padding: 16,
    marginBottom: 12,
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
    marginBottom: 16,
  },
  courseCode: {
    fontSize: 18,
    fontWeight: '700',
    color: '#111827',
  },
  courseName: {
    fontSize: 14,
    color: '#6B7280',
    marginTop: 2,
    maxWidth: 200,
  },
  gradeCircle: {
    alignItems: 'center',
  },
  gradeValue: {
    fontSize: 28,
    fontWeight: '700',
  },
  letterGrade: {
    fontSize: 14,
    fontWeight: '600',
    color: '#9CA3AF',
  },
  assignmentsList: {
    borderTopWidth: 1,
    borderTopColor: '#F3F4F6',
    paddingTop: 12,
    gap: 12,
  },
  assignmentRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  assignmentName: {
    fontSize: 14,
    fontWeight: '500',
    color: '#374151',
  },
  assignmentDate: {
    fontSize: 12,
    color: '#9CA3AF',
    marginTop: 2,
  },
  scoreContainer: {
    alignItems: 'flex-end',
    minWidth: 100,
  },
  scoreText: {
    fontSize: 14,
    fontWeight: '600',
    color: '#374151',
  },
  scoreBar: {
    width: 80,
    height: 4,
    backgroundColor: '#E5E7EB',
    borderRadius: 2,
    marginTop: 4,
    overflow: 'hidden',
  },
  scoreFill: {
    height: '100%',
    borderRadius: 2,
  },
});
