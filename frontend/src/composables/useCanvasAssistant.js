import { computed, ref, unref } from 'vue'
import { canvasAssistantService } from '@/services/canvasAssistant'
import { apiKeysService } from '@/services/apiKeys'

const normalizeSelectedItemIds = (value) =>
  [...new Set((Array.isArray(value) ? value : []).map((item) => String(item || '').trim()).filter(Boolean))]

const buildMessageId = (prefix, turnId) => `${prefix}-${turnId}-${Date.now()}`

export function useCanvasAssistant({
  documentId = '',
  selectedItemIds = [],
  service = canvasAssistantService,
  onMutationApplied = null
} = {}) {
  const sessionId = ref('')
  const status = ref('idle')
  const error = ref('')
  const messages = ref([])
  const stepEvents = ref([])
  const toolTrace = ref([])
  const pendingInterrupt = ref(null)
  const isStreaming = ref(false)
  const apiKeysLoading = ref(false)
  const chatModelsLoading = ref(false)
  const apiKeyOptions = ref([])
  const chatModelOptions = ref([])
  const selectedApiKeyId = ref('')
  const selectedChatModelId = ref('')
  const draftSelectedItemIds = ref([])
  const currentTurnId = ref(0)
  const currentAssistantMessageId = ref('')
  const abortController = ref(null)
  const turnMutationApplied = ref(false)

  const resolvedDocumentId = computed(() => String(unref(documentId) || '').trim())
  const resolvedSelectedItemIds = computed(() => normalizeSelectedItemIds(unref(selectedItemIds)))

  const canSend = computed(
    () =>
      !isStreaming.value &&
      !pendingInterrupt.value &&
      Boolean(selectedApiKeyId.value) &&
      Boolean(selectedChatModelId.value) &&
      Boolean(resolvedDocumentId.value)
  )

  const normalizeApiKeyOptions = (response) => {
    const apiKeys = Array.isArray(response?.api_keys) ? response.api_keys : []
    return apiKeys
      .map((item) => ({
        id: String(item?.id || '').trim(),
        label: String(item?.name || item?.id || '').trim(),
        provider: String(item?.provider || '').trim()
      }))
      .filter((item) => item.id)
  }

  const normalizeModelOptions = (response) => {
    const rawModels = Array.isArray(response) ? response : Array.isArray(response?.models) ? response.models : []
    return rawModels.map((item) => String(item || '').trim()).filter(Boolean)
  }

  const loadChatModels = async (apiKeyId) => {
    const normalizedApiKeyId = String(apiKeyId || '').trim()
    chatModelsLoading.value = true
    try {
      if (!normalizedApiKeyId) {
        chatModelOptions.value = []
        selectedChatModelId.value = ''
        return []
      }
      const models = normalizeModelOptions(await apiKeysService.getAPIKeyModels(normalizedApiKeyId, 'text'))
      chatModelOptions.value = models
      if (!models.includes(selectedChatModelId.value)) {
        selectedChatModelId.value = models[0] || ''
      }
      return models
    } finally {
      chatModelsLoading.value = false
    }
  }

  const loadApiKeys = async () => {
    apiKeysLoading.value = true
    try {
      const options = normalizeApiKeyOptions(
        await apiKeysService.getAPIKeys({ page: 1, size: 100, key_status: 'active' })
      )
      apiKeyOptions.value = options
      if (!options.some((item) => item.id === selectedApiKeyId.value)) {
        selectedApiKeyId.value = options[0]?.id || ''
      }
      await loadChatModels(selectedApiKeyId.value)
      return options
    } finally {
      apiKeysLoading.value = false
    }
  }

  const appendMessage = (message) => {
    const id = String(message.id || buildMessageId('message', currentTurnId.value)).trim()
    const nextDelta = typeof message.delta === 'string' ? message.delta : ''
    const nextMessage = {
      id,
      role: String(message.role || 'assistant').trim() === 'user' ? 'user' : 'assistant',
      content: String(message.content ?? nextDelta ?? ''),
      order: Number.isFinite(Number(message.order)) ? Number(message.order) : messages.value.length + 1
    }
    const existingIndex = messages.value.findIndex((item) => item.id === id)
    if (existingIndex >= 0) {
      messages.value = messages.value.map((item, index) =>
        index === existingIndex
          ? {
              ...item,
              ...nextMessage,
              content: nextDelta && nextMessage.role === 'assistant'
                ? `${String(item.content ?? '')}${nextDelta}`
                : nextMessage.content || item.content
            }
          : item
      )
      return nextMessage
    }
    messages.value = [...messages.value, nextMessage]
    return nextMessage
  }

  const upsertStep = (step = {}) => {
    const id = String(step.id || buildMessageId('step', currentTurnId.value)).trim()
    const nextStep = {
      id,
      title: String(step.title || '').trim(),
      status: String(step.status || 'running').trim() || 'running',
      order: Number.isFinite(Number(step.order)) ? Number(step.order) : stepEvents.value.length + 1
    }
    const existingIndex = stepEvents.value.findIndex((item) => item.id === id)
    if (existingIndex >= 0) {
      stepEvents.value = stepEvents.value.map((item, index) => (index === existingIndex ? { ...item, ...nextStep } : item))
      return
    }
    stepEvents.value = [...stepEvents.value, nextStep]
  }

  const upsertToolCall = (toolCall = {}) => {
    const id = String(toolCall.id || buildMessageId('tool', currentTurnId.value)).trim()
    const nextTool = {
      id,
      toolName: String(toolCall.toolName || '').trim(),
      status: String(toolCall.status || 'completed').trim() || 'completed',
      args: toolCall.args ?? null,
      result: toolCall.result ?? null,
      order: Number.isFinite(Number(toolCall.order)) ? Number(toolCall.order) : toolTrace.value.length + 1
    }
    const existingIndex = toolTrace.value.findIndex((item) => item.id === id || item.toolName === nextTool.toolName)
    if (existingIndex >= 0) {
      toolTrace.value = toolTrace.value.map((item, index) => (index === existingIndex ? { ...item, ...nextTool } : item))
      return
    }
    toolTrace.value = [...toolTrace.value, nextTool]
  }

  const applyEvent = (event) => {
    if (!event || typeof event !== 'object') return
    if (event.kind === 'session') {
      sessionId.value = String(event.sessionId || '').trim()
      return
    }
    if (event.kind === 'thinking') {
      upsertStep({ id: 'step-thinking', title: 'Thinking', status: 'running' })
      return
    }
    if (event.kind === 'step') {
      upsertStep(event.step || {})
      return
    }
    if (event.kind === 'tool') {
      const effect = event.toolCall?.result?.effect || event.toolCall?.result?.summary || event.toolCall?.result || null
      if (
        effect &&
        typeof effect === 'object' &&
        (effect.mutated === true ||
          effect.created_item_ids?.length > 0 ||
          effect.updated_item_ids?.length > 0 ||
          effect.deleted_item_ids?.length > 0 ||
          effect.created_connection_ids?.length > 0 ||
          effect.deleted_connection_ids?.length > 0 ||
          effect.submitted_task_ids?.length > 0)
      ) {
        turnMutationApplied.value = true
      }
      upsertToolCall(event.toolCall || {})
      return
    }
    if (event.kind === 'message') {
      const message = event.message || {}
      if (message.role === 'assistant' && currentAssistantMessageId.value) {
        appendMessage({ ...message, id: message.id || currentAssistantMessageId.value })
      } else {
        const normalized = appendMessage(message)
        if (normalized.role === 'assistant') {
          currentAssistantMessageId.value = normalized.id
        }
      }
      return
    }
    if (event.kind === 'interrupt') {
      pendingInterrupt.value = {
        interruptId: String(event.interrupt?.interruptId || '').trim(),
        sessionId: String(event.interrupt?.sessionId || sessionId.value || '').trim(),
        kind: String(event.interrupt?.kind || '').trim(),
        title: String(event.interrupt?.title || '').trim(),
        message: String(event.interrupt?.message || '').trim(),
        actions: Array.isArray(event.interrupt?.actions) ? event.interrupt.actions : [],
        selectedModelId: String(event.interrupt?.selectedModelId || '').trim(),
        modelOptions: Array.isArray(event.interrupt?.modelOptions) ? event.interrupt.modelOptions : [],
        scopeItemIds: normalizeSelectedItemIds(event.interrupt?.scopeItemIds || draftSelectedItemIds.value)
      }
      status.value = 'awaiting_interrupt'
      return
    }
    if (event.kind === 'error') {
      error.value = String(event.message || 'assistant request failed').trim()
      status.value = 'error'
      isStreaming.value = false
      return
    }
    if (event.kind === 'done') {
      isStreaming.value = false
      if (!pendingInterrupt.value) {
        status.value = 'idle'
      }
    }
  }

  const runTurn = async (turnRunner) => {
    abortController.value?.abort?.()
    abortController.value = new AbortController()
    isStreaming.value = true
    status.value = 'streaming'
    error.value = ''
    turnMutationApplied.value = false
    try {
      const result = await turnRunner(abortController.value.signal)
      if (!pendingInterrupt.value && status.value === 'streaming') {
        status.value = 'idle'
      }
      return result
    } catch (turnError) {
      error.value = turnError?.message || 'assistant request failed'
      status.value = 'error'
      throw turnError
    } finally {
      isStreaming.value = false
      abortController.value = null
    }
  }

  const sendMessage = async (message) => {
    const trimmedMessage = String(message || '').trim()
    if (!trimmedMessage || !canSend.value) {
      return false
    }

    const selectedItemIdsSnapshot = resolvedSelectedItemIds.value
    draftSelectedItemIds.value = selectedItemIdsSnapshot
    currentTurnId.value += 1
    currentAssistantMessageId.value = ''

    appendMessage({
      id: buildMessageId('user', currentTurnId.value),
      role: 'user',
      content: trimmedMessage,
      order: messages.value.length + 1
    })

    await runTurn((signal) =>
      service.chat(
        {
          documentId: resolvedDocumentId.value,
          sessionId: sessionId.value,
          message: trimmedMessage,
          apiKeyId: selectedApiKeyId.value,
          chatModelId: selectedChatModelId.value,
          selectedItemIds: selectedItemIdsSnapshot
        },
        { onEvent: applyEvent, signal }
      )
    )
    return true
  }

  const updatePendingInterruptModelId = (selectedModelId) => {
    if (!pendingInterrupt.value) return
    pendingInterrupt.value = { ...pendingInterrupt.value, selectedModelId: String(selectedModelId || '').trim() }
  }

  const resumeInterrupt = async ({ decision = 'approve', selectedModelId = '' } = {}) => {
    if (!pendingInterrupt.value || isStreaming.value) {
      return false
    }
    const interruptSnapshot = pendingInterrupt.value
    const selectedItemIdsSnapshot = interruptSnapshot.scopeItemIds.length > 0 ? interruptSnapshot.scopeItemIds : draftSelectedItemIds.value
    updatePendingInterruptModelId(selectedModelId)
    await runTurn((signal) =>
      service.resume(
        {
          documentId: resolvedDocumentId.value,
          sessionId: interruptSnapshot.sessionId || sessionId.value,
          interruptId: interruptSnapshot.interruptId,
          decision,
          selectedModelId: pendingInterrupt.value.selectedModelId,
          selectedItemIds: selectedItemIdsSnapshot
        },
        { onEvent: applyEvent, signal }
      )
    )
    if (decision === 'approve' && turnMutationApplied.value) {
      try {
        await Promise.resolve(
          onMutationApplied?.({
            documentId: resolvedDocumentId.value,
            selectedItemIds: selectedItemIdsSnapshot,
            sessionId: interruptSnapshot.sessionId || sessionId.value,
            interruptId: interruptSnapshot.interruptId
          })
        )
      } catch (refreshError) {
        console.error('Refresh canvas after assistant mutation failed', refreshError)
      }
    }
    pendingInterrupt.value = null
    status.value = 'idle'
    return true
  }

  const reset = () => {
    abortController.value?.abort?.()
    sessionId.value = ''
    status.value = 'idle'
    error.value = ''
    messages.value = []
    stepEvents.value = []
    toolTrace.value = []
    pendingInterrupt.value = null
    isStreaming.value = false
    draftSelectedItemIds.value = []
    currentTurnId.value = 0
    currentAssistantMessageId.value = ''
    turnMutationApplied.value = false
  }

  loadApiKeys().catch(() => {
    error.value = '加载 assistant 对话模型失败'
  })

  return {
    sessionId,
    status,
    error,
    messages,
    stepEvents,
    toolTrace,
    pendingInterrupt,
    apiKeysLoading,
    chatModelsLoading,
    apiKeyOptions,
    chatModelOptions,
    selectedApiKeyId,
    selectedChatModelId,
    isStreaming,
    canSend,
    sendMessage,
    updateSelectedApiKeyId: async (apiKeyId) => {
      selectedApiKeyId.value = String(apiKeyId || '').trim()
      await loadChatModels(selectedApiKeyId.value)
    },
    updateSelectedChatModelId: (chatModelId) => {
      selectedChatModelId.value = String(chatModelId || '').trim()
    },
    resumeInterrupt,
    updatePendingInterruptModelId,
    reset
  }
}

export default useCanvasAssistant
