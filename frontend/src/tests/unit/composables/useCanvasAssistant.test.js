/**
 * @vitest-environment jsdom
 */

import { createApp, defineComponent, nextTick, ref } from 'vue'
import { beforeEach, describe, expect, it, vi } from 'vitest'

vi.mock('@/services/canvasAssistant', () => ({
  canvasAssistantService: {
    chat: vi.fn(async (_payload, handlers) => {
      handlers?.onEvent?.({ kind: 'session', sessionId: 'session-1' })
      handlers?.onEvent?.({ kind: 'step', step: { id: 'step-plan', title: 'Plan turn', status: 'running', order: 1 } })
      handlers?.onEvent?.({ kind: 'tool', toolCall: { id: 'tool-1', toolName: 'canvas.update_items', status: 'running', order: 2 } })
      handlers?.onEvent?.({
        kind: 'interrupt',
        interrupt: {
          interruptId: 'interrupt-1',
          sessionId: 'session-1',
          kind: 'confirm_execute',
          title: '确认执行',
          message: '请选择后继续',
          actions: ['approve', 'reject'],
          scopeItemIds: ['item-1'],
          selectedModelId: ''
        }
      })
      handlers?.onDone?.()
      return { events: [] }
    }),
    resume: vi.fn(async (_payload, handlers) => {
      handlers?.onEvent?.({ kind: 'tool', toolCall: { id: 'tool-1', toolName: 'canvas.update_items', status: 'completed', result: { updated: 1 }, order: 3 } })
      handlers?.onEvent?.({ kind: 'message', message: { id: 'assistant-1', role: 'assistant', delta: '已完成 1 个操作，并同步最新画布状态。', order: 4 } })
      handlers?.onDone?.()
      return { events: [] }
    })
  }
}))

vi.mock('@/services/apiKeys', () => ({
  apiKeysService: {
    getAPIKeys: vi.fn().mockResolvedValue({
      api_keys: [{ id: 'key-1', name: '主 Key', provider: 'openai' }]
    }),
    getAPIKeyModels: vi.fn().mockResolvedValue(['gpt-4o-mini'])
  }
}))

const mountComposable = (selectedItemIds = ref(['item-1'])) => {
  let assistant = null
  const app = createApp(
    defineComponent({
      setup() {
        assistant = useCanvasAssistant({
          documentId: ref('doc-1'),
          selectedItemIds
        })
        return () => null
      }
    })
  )
  app.mount(document.createElement('div'))
  return { app, get assistant() { return assistant } }
}

import { useCanvasAssistant } from '@/composables/useCanvasAssistant'
import { canvasAssistantService } from '@/services/canvasAssistant'

describe('useCanvasAssistant', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('tracks tool trace and interrupt state using the new agent protocol', async () => {
    const selectedItemIds = ref(['item-1'])
    const { app, assistant } = mountComposable(selectedItemIds)
    await nextTick()
    await Promise.resolve()
    await Promise.resolve()

    await assistant.sendMessage('更新这个节点')
    await nextTick()

    expect(canvasAssistantService.chat).toHaveBeenCalledWith(
      expect.objectContaining({
        documentId: 'doc-1',
        message: '更新这个节点',
        selectedItemIds: ['item-1']
      }),
      expect.any(Object)
    )
    expect(assistant.pendingInterrupt.value).toMatchObject({
      interruptId: 'interrupt-1',
      kind: 'confirm_execute'
    })
    expect(assistant.stepEvents.value.map((item) => item.id)).toEqual(['step-plan'])
    expect(assistant.toolTrace.value[0]).toMatchObject({
      toolName: 'canvas.update_items',
      status: 'running'
    })
    expect(assistant.canSend.value).toBe(false)

    selectedItemIds.value = ['item-2']
    await assistant.resumeInterrupt({
      decision: 'approve',
      selectedModelId: 'model-a'
    })
    await nextTick()

    expect(canvasAssistantService.resume).toHaveBeenCalledWith(
      expect.objectContaining({
        documentId: 'doc-1',
        sessionId: 'session-1',
        interruptId: 'interrupt-1',
        decision: 'approve',
        selectedModelId: 'model-a',
        selectedItemIds: ['item-1']
      }),
      expect.any(Object)
    )
    expect(assistant.messages.value.at(-1)).toMatchObject({
      role: 'assistant',
      content: '已完成 1 个操作，并同步最新画布状态。'
    })

    app.unmount()
  })
})
