import { View, Text, StyleSheet, ScrollView, TextInput, TouchableOpacity, KeyboardAvoidingView, Platform } from 'react-native'
import { useState, useRef } from 'react'
import { useAuth } from '@clerk/clerk-expo'

interface Message {
  id: string
  role: 'user' | 'assistant'
  content: string
}

export default function CoachScreen() {
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState('')
  const [isStreaming, setIsStreaming] = useState(false)
  const sessionId = useRef(Math.random().toString(36)).current
  const { getToken } = useAuth()
  const scrollRef = useRef<ScrollView>(null)

  const sendMessage = async () => {
    if (!input.trim() || isStreaming) return
    const text = input
    setInput('')
    const userMsg: Message = { id: Math.random().toString(36), role: 'user', content: text }
    const assistantId = Math.random().toString(36)
    setMessages((prev) => [...prev, userMsg, { id: assistantId, role: 'assistant', content: '' }])
    setIsStreaming(true)

    try {
      const token = await getToken()
      const res = await fetch(`${process.env['EXPO_PUBLIC_API_URL']}/api/v1/ai/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
        body: JSON.stringify({ message: text, sessionId, messageType: 'COACHING' }),
      })

      if (!res.body) return
      const reader = res.body.getReader()
      const decoder = new TextDecoder()

      while (true) {
        const { done, value } = await reader.read()
        if (done) break
        const chunk = decoder.decode(value)
        const lines = chunk.split('\n').filter((l) => l.startsWith('data: '))
        for (const line of lines) {
          try {
            const json = JSON.parse(line.slice(6)) as { type: string; text?: string }
            if (json.type === 'delta' && json.text) {
              setMessages((prev) => prev.map((m) => m.id === assistantId ? { ...m, content: m.content + (json.text ?? '') } : m))
            }
          } catch {}
        }
      }
    } finally {
      setIsStreaming(false)
    }
  }

  return (
    <KeyboardAvoidingView style={styles.container} behavior={Platform.OS === 'ios' ? 'padding' : undefined}>
      <View style={styles.header}>
        <Text style={styles.title}>AI Coach</Text>
        <Text style={styles.subtitle}>Judgment-free. Always here.</Text>
      </View>

      <ScrollView
        ref={scrollRef}
        style={styles.messages}
        contentContainerStyle={styles.messagesContent}
        onContentSizeChange={() => scrollRef.current?.scrollToEnd({ animated: true })}
      >
        {messages.length === 0 && (
          <View style={styles.empty}>
            <Text style={styles.emptyEmoji}>💬</Text>
            <Text style={styles.emptyText}>Share what's on your mind. No judgment, ever.</Text>
          </View>
        )}
        {messages.map((msg) => (
          <View key={msg.id} style={[styles.bubble, msg.role === 'user' ? styles.bubbleUser : styles.bubbleAssistant]}>
            <Text style={[styles.bubbleText, msg.role === 'user' && styles.bubbleTextUser]}>{msg.content}</Text>
          </View>
        ))}
        {isStreaming && <Text style={styles.typing}>ClearPath is typing...</Text>}
      </ScrollView>

      <View style={styles.inputRow}>
        <TextInput
          style={styles.input}
          value={input}
          onChangeText={setInput}
          placeholder="Message..."
          multiline
          maxLength={1000}
        />
        <TouchableOpacity
          style={[styles.sendBtn, (!input.trim() || isStreaming) && styles.sendBtnDisabled]}
          onPress={sendMessage}
          disabled={!input.trim() || isStreaming}
        >
          <Text style={styles.sendText}>↑</Text>
        </TouchableOpacity>
      </View>
    </KeyboardAvoidingView>
  )
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: 'white' },
  header: { paddingHorizontal: 20, paddingTop: 60, paddingBottom: 16, borderBottomWidth: 1, borderBottomColor: '#f3f4f6' },
  title: { fontSize: 22, fontWeight: 'bold', color: '#111827' },
  subtitle: { fontSize: 13, color: '#6b7280', marginTop: 2 },
  messages: { flex: 1 },
  messagesContent: { padding: 16, gap: 12, paddingBottom: 8 },
  empty: { alignItems: 'center', paddingVertical: 48 },
  emptyEmoji: { fontSize: 40, marginBottom: 12 },
  emptyText: { fontSize: 15, color: '#6b7280', textAlign: 'center' },
  bubble: { maxWidth: '80%', borderRadius: 18, padding: 12 },
  bubbleUser: { backgroundColor: '#16a34a', alignSelf: 'flex-end', borderBottomRightRadius: 4 },
  bubbleAssistant: { backgroundColor: '#f3f4f6', alignSelf: 'flex-start', borderBottomLeftRadius: 4 },
  bubbleText: { fontSize: 15, color: '#111827', lineHeight: 22 },
  bubbleTextUser: { color: 'white' },
  typing: { fontSize: 13, color: '#9ca3af', fontStyle: 'italic', paddingLeft: 8 },
  inputRow: { flexDirection: 'row', gap: 8, padding: 12, borderTopWidth: 1, borderTopColor: '#f3f4f6', alignItems: 'flex-end' },
  input: { flex: 1, borderWidth: 1, borderColor: '#e5e7eb', borderRadius: 20, paddingHorizontal: 16, paddingVertical: 10, fontSize: 15, maxHeight: 100 },
  sendBtn: { width: 40, height: 40, borderRadius: 20, backgroundColor: '#16a34a', alignItems: 'center', justifyContent: 'center' },
  sendBtnDisabled: { backgroundColor: '#d1d5db' },
  sendText: { color: 'white', fontSize: 18, fontWeight: 'bold' },
})
