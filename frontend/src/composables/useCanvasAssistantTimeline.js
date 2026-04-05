import { computed, unref } from 'vue'

const readOrder = (value, fallback = 0) => {
  const parsed = Number(value)
  return Number.isFinite(parsed) ? parsed : fallback
}

const normalizeMessageItem = (message = {}, fallbackOrder = 0) => ({
  id: String(message.id || `message-${fallbackOrder}`).trim(),
  type: `${String(message.role || 'assistant').trim() === 'user' ? 'user' : 'assistant'}_message`,
  order: readOrder(message.order, fallbackOrder),
  message: {
    id: String(message.id || `message-${fallbackOrder}`).trim(),
    role: String(message.role || 'assistant').trim() === 'user' ? 'user' : 'assistant',
    content: String(message.content || '').trim()
  }
})

const normalizeActivityItem = (activity = {}, fallbackOrder = 0, activityType = 'step') => ({
  id: String(activity.id || `${activityType}-${fallbackOrder}`).trim(),
  type: 'activity',
  order: readOrder(activity.order, fallbackOrder),
  activity: {
    id: String(activity.id || `${activityType}-${fallbackOrder}`).trim(),
    activityType,
    title: String(activity.title || '').trim(),
    toolName: String(activity.toolName || '').trim(),
    status: String(activity.status || 'completed').trim() || 'completed',
    args: activity.args ?? null,
    result: activity.result ?? null
  }
})

const normalizeInterruptItem = (interrupt = {}, fallbackOrder = 0) => ({
  id: String(interrupt.interruptId || `interrupt-${fallbackOrder}`).trim(),
  type: 'interrupt_card',
  order: readOrder(interrupt.order, fallbackOrder),
  interrupt: {
    interruptId: String(interrupt.interruptId || '').trim(),
    sessionId: String(interrupt.sessionId || '').trim(),
    kind: String(interrupt.kind || '').trim(),
    title: String(interrupt.title || '').trim(),
    message: String(interrupt.message || '').trim(),
    actions: Array.isArray(interrupt.actions) ? interrupt.actions : [],
    selectedModelId: String(interrupt.selectedModelId || '').trim(),
    modelOptions: Array.isArray(interrupt.modelOptions) ? interrupt.modelOptions : [],
    scopeItemIds: Array.isArray(interrupt.scopeItemIds) ? interrupt.scopeItemIds : []
  }
})

const normalizeErrorItem = (message = '', order = Number.MAX_SAFE_INTEGER) => ({
  id: 'assistant-error',
  type: 'error_notice',
  order,
  message: String(message || '').trim()
})

export const buildCanvasAssistantTimelineItems = ({
  messages = [],
  stepEvents = [],
  toolTrace = [],
  pendingInterrupt = null,
  error = ''
} = {}) => {
  const items = []
  const normalizedMessages = (Array.isArray(messages) ? messages : []).map((message, index) => normalizeMessageItem(message, index + 1))
  const normalizedSteps = (Array.isArray(stepEvents) ? stepEvents : []).map((step, index) => normalizeActivityItem(step, normalizedMessages.length + index + 1, 'step'))
  const normalizedTools = (Array.isArray(toolTrace) ? toolTrace : []).map((tool, index) => normalizeActivityItem(tool, normalizedMessages.length + normalizedSteps.length + index + 1, 'tool'))

  items.push(...normalizedMessages, ...normalizedSteps, ...normalizedTools)
  if (pendingInterrupt) {
    items.push(normalizeInterruptItem(pendingInterrupt, items.length + 1))
  }
  if (String(error || '').trim()) {
    items.push(normalizeErrorItem(error, items.length + 1))
  }
  return [...items].sort((left, right) => readOrder(left.order) - readOrder(right.order))
}

export function useCanvasAssistantTimeline(source = {}) {
  const timelineItems = computed(() =>
    buildCanvasAssistantTimelineItems({
      messages: unref(source.messages) || [],
      stepEvents: unref(source.stepEvents) || [],
      toolTrace: unref(source.toolTrace) || [],
      pendingInterrupt: unref(source.pendingInterrupt) || null,
      error: unref(source.error) || ''
    })
  )

  return { timelineItems }
}

export default useCanvasAssistantTimeline
