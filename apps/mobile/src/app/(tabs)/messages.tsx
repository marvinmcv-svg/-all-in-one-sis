import { useState, useEffect } from "react"
import { View, Text, FlatList, TouchableOpacity, StyleSheet, RefreshControl } from "react-native"
import { apiClient } from "../../lib/api"

interface Message {
  id: number
  sender: { name: string; email: string }
  subject: string
  body: string
  sent_at: string
  is_read: boolean
}

export default function Messages() {
  const [messages, setMessages] = useState<Message[]>([])
  const [loading, setLoading] = useState(true)
  const [refreshing, setRefreshing] = useState(false)

  const fetchMessages = async () => {
    try {
      const response = await apiClient.get<Message[]>("messages")
      setMessages(response)
    } catch (err) {
      console.error("Failed to fetch messages:", err)
    } finally {
      setLoading(false)
      setRefreshing(false)
    }
  }

  useEffect(() => {
    fetchMessages()
  }, [])

  const onRefresh = () => {
    setRefreshing(true)
    fetchMessages()
  }

  const renderMessage = ({ item }: { item: Message }) => (
    <TouchableOpacity style={[styles.messageCard, !item.is_read && styles.unread]}>
      <View style={styles.messageHeader}>
        <Text style={styles.sender}>{item.sender.name}</Text>
        <Text style={styles.date}>
          {new Date(item.sent_at).toLocaleDateString()}
        </Text>
      </View>
      <Text style={styles.subject}>{item.subject}</Text>
      <Text style={styles.body} numberOfLines={2}>{item.body}</Text>
    </TouchableOpacity>
  )

  if (loading) {
    return (
      <View style={styles.centered}>
        <Text>Loading messages...</Text>
      </View>
    )
  }

  return (
    <View style={styles.container}>
      <FlatList
        data={messages}
        keyExtractor={(item) => String(item.id)}
        renderItem={renderMessage}
        refreshControl={
          <RefreshControl refreshing={refreshing} onRefresh={onRefresh} />
        }
        ListEmptyComponent={
          <View style={styles.empty}>
            <Text>No messages yet</Text>
          </View>
        }
      />
    </View>
  )
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: "#f5f5f5",
  },
  centered: {
    flex: 1,
    justifyContent: "center",
    alignItems: "center",
  },
  messageCard: {
    backgroundColor: "#fff",
    padding: 16,
    marginHorizontal: 16,
    marginVertical: 8,
    borderRadius: 8,
    shadowColor: "#000",
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.1,
    shadowRadius: 2,
    elevation: 2,
  },
  unread: {
    borderLeftWidth: 4,
    borderLeftColor: "#3b82f6",
  },
  messageHeader: {
    flexDirection: "row",
    justifyContent: "space-between",
    marginBottom: 4,
  },
  sender: {
    fontWeight: "600",
    fontSize: 16,
  },
  date: {
    color: "#666",
    fontSize: 12,
  },
  subject: {
    fontSize: 14,
    color: "#333",
    marginBottom: 4,
  },
  body: {
    fontSize: 14,
    color: "#666",
  },
  empty: {
    flex: 1,
    justifyContent: "center",
    alignItems: "center",
    padding: 40,
  },
})