import Anthropic from '@anthropic-ai/sdk'
import type { AIMessage } from '@clearpath/shared-types'

const anthropic = new Anthropic({ apiKey: process.env['ANTHROPIC_API_KEY'] })

const SYSTEM_PROMPT = `You are ClearPath, a compassionate, evidence-based AI recovery coach
specializing in nicotine vaping and cannabis cessation.

Core principles:
1. NEVER shame or judge the user for using or relapsing
2. Ground responses in CBT (Cognitive Behavioral Therapy) and Motivational Interviewing
3. Be warm, direct, and concise — max 3 short paragraphs unless doing a CBT exercise
4. When user expresses a craving: validate → distract → breathe → reframe (in that order)
5. When user relapses: normalize → explore triggers → rebuild motivation → next step
6. In crisis (self-harm language detected): immediately provide 988 Suicide & Crisis Lifeline,
   express care, do NOT try to handle clinical crisis alone

Substance knowledge:
- Nicotine: receptor downregulation, dopamine system, 72hr peak withdrawal, 3-week physical clear
- Cannabis: CB1 receptor reset takes 28 days, psychological dependence, sleep disruption 1–2 weeks
- Dual users: address both simultaneously; nicotine withdrawal is often more acute

Response style: conversational, no bullet points unless asked, never preachy.`

export async function streamCoachResponse(
  userId: string,
  messages: Pick<AIMessage, 'role' | 'content'>[],
  messageType: AIMessage['messageType'] = 'COACHING',
  userContext: { substanceType: string; daysClean: number; lastCraving?: string }
): Promise<ReadableStream<string>> {
  const contextNote = `[Context: user is ${userContext.daysClean} days clean from ${userContext.substanceType}${userContext.lastCraving ? `, last craving logged: ${userContext.lastCraving}` : ''}]`

  const stream = await anthropic.messages.create({
    model: 'claude-sonnet-4-20250514',
    max_tokens: 1000,
    system: SYSTEM_PROMPT + '\n\n' + contextNote,
    messages: messages.map((m) => ({ role: m.role, content: m.content })),
    stream: true,
  })

  return new ReadableStream({
    async start(controller) {
      for await (const event of stream) {
        if (event.type === 'content_block_delta' && event.delta.type === 'text_delta') {
          controller.enqueue(event.delta.text)
        }
      }
      controller.close()
    }
  })
}

export async function generateCBTFeedback(
  exerciseType: string,
  userResponse: string,
  weekNumber: number
): Promise<string> {
  const msg = await anthropic.messages.create({
    model: 'claude-sonnet-4-20250514',
    max_tokens: 600,
    system: `You are a CBT therapist assistant reviewing a Week ${weekNumber} exercise (${exerciseType}).
    Give warm, specific, actionable feedback in 2–3 short paragraphs.
    Acknowledge what the user did well, then gently offer one growth reflection.`,
    messages: [{ role: 'user', content: userResponse }],
  })
  const first = msg.content[0]
  return first?.type === 'text' ? first.text : ''
}
