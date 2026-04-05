/**
 * @vitest-environment jsdom
 */

import { computed, ref } from 'vue'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import CanvasAssistant from '@/components/canvas/assistant/CanvasAssistant.vue'
import { useCanvasAssistant } from '@/composables/useCanvasAssistant'
import { useCanvasAssistantTimeline } from '@/composables/useCanvasAssistantTimeline'

vi.mock('@/composables/useCanvasAssistant', () => {
  const useCanvasAssistant = vi.fn()
  return {
    useCanvasAssistant,
    default: useCanvasAssistant
  }
})

vi.mock('@/composables/useCanvasAssistantTimeline', () => {
  const useCanvasAssistantTimeline = vi.fn()
  return {
    useCanvasAssistantTimeline,
    default: useCanvasAssistantTimeline
  }
})

describe('CanvasAssistant', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders the assistant rail and forwards composer and confirmation actions', async () => {
    const sendMessage = vi.fn()
    const resumeConfirmation = vi.fn()
    const updatePendingConfirmationModelId = vi.fn()
    const reset = vi.fn()

    useCanvasAssistant.mockReturnValue({
      sessionId: ref('session-1'),
      status: ref('awaiting_interrupt'),
      error: ref(''),
      messages: ref([
        { id: 'm-1', role: 'user', content: '请看一下', order: 1 }
      ]),
      stepEvents: ref([
        {
          id: 'step-1',
          title: 'Plan turn',
          status: 'completed',
          order: 2
        }
      ]),
      toolTrace: ref([
        {
          id: 't-1',
          toolName: 'canvas.update_items',
          status: 'completed',
          args: { updates: [{ itemId: 'item-1' }] },
          result: { updated: 1 },
          order: 3
        }
      ]),
      pendingInterrupt: ref({
        interruptId: 'interrupt-1',
        sessionId: 'session-1',
        kind: 'confirm_execute',
        title: '确认执行',
        message: '请选择模型后继续',
        selectedModelId: '',
        scopeItemIds: ['item-1'],
        modelOptions: [
          { modelId: 'model-a', label: '模型 A', resolution: '1024x1024' }
        ],
        actions: ['approve', 'reject']
      }),
      apiKeyOptions: ref([
        { id: 'key-1', label: '主 Key', provider: 'openai' }
      ]),
      chatModelOptions: ref(['gpt-4o-mini', 'gpt-4o']),
      selectedApiKeyId: ref('key-1'),
      selectedChatModelId: ref('gpt-4o-mini'),
      apiKeysLoading: ref(false),
      chatModelsLoading: ref(false),
      isStreaming: ref(false),
      canSend: ref(true),
      sendMessage,
      updateSelectedApiKeyId: vi.fn(),
      updateSelectedChatModelId: vi.fn(),
      resumeInterrupt: resumeConfirmation,
      updatePendingInterruptModelId: updatePendingConfirmationModelId,
      reset
    })

    useCanvasAssistantTimeline.mockReturnValue({
      timelineItems: computed(() => [
        {
          id: 'm-1',
          type: 'user_message',
          message: { role: 'user', content: '请看一下', order: 1 }
        },
        {
          id: 'step-1',
          type: 'activity',
          activity: {
            activityType: 'step',
            title: 'Plan turn',
            status: 'completed',
            args: null,
            result: null
          }
        },
        {
          id: 't-1',
          type: 'activity',
          activity: {
            activityType: 'tool',
            toolName: 'canvas.update_items',
            status: 'completed',
            args: { updates: [{ itemId: 'item-1' }] },
            result: { updated: 1 }
          }
        },
        {
          id: 'i-1',
          type: 'interrupt_card',
          interrupt: {
            interruptId: 'interrupt-1',
            kind: 'confirm_execute',
            title: '确认执行',
            message: '请选择模型后继续',
            selectedModelId: '',
            scopeItemIds: ['item-1'],
            modelOptions: [
              { modelId: 'model-a', label: '模型 A', resolution: '1024x1024' }
            ],
            actions: ['approve', 'reject']
          }
        }
      ])
    })

    const wrapper = mount(CanvasAssistant, {
      props: {
        documentId: 'doc-1',
        selectedItemIds: ['item-1']
      }
    })

    expect(wrapper.text()).toContain('AI 助手')
    expect(wrapper.text()).toContain('Session session-1')
    expect(wrapper.text()).toContain('请看一下')
    expect(wrapper.text()).toContain('canvas.update_items')
    expect(wrapper.text()).toContain('确认执行')
    expect(wrapper.find('[data-testid="assistant-api-key-select"]').exists()).toBe(true)
    expect(wrapper.find('[data-testid="assistant-chat-model-select"]').exists()).toBe(true)

    await wrapper.find('textarea').setValue('请处理选中的节点')
    await wrapper.find('form').trigger('submit.prevent')
    expect(sendMessage).toHaveBeenCalledWith('请处理选中的节点')

    await wrapper.find('select').setValue('model-a')
    expect(updatePendingConfirmationModelId).toHaveBeenCalledWith('model-a')

    await wrapper.find('.assistant-confirmation__button--primary').trigger('click')
    expect(resumeConfirmation).toHaveBeenCalledWith({
      decision: 'approve',
      selectedModelId: 'model-a'
    })

    await wrapper.find('.assistant-header__reset').trigger('click')
    expect(reset).toHaveBeenCalled()
  })
})
