/**
 * @vitest-environment jsdom
 */

import { nextTick, ref } from 'vue'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import CanvasEditor from '@/views/canvas/CanvasEditor.vue'
import { useCanvasEditor } from '@/composables/useCanvasEditor'
import { useCanvasGeneration } from '@/composables/useCanvasGeneration'

vi.mock('@/composables/useCanvasEditor', () => ({
  useCanvasEditor: vi.fn(),
  default: vi.fn()
}))

vi.mock('@/composables/useCanvasGeneration', () => ({
  useCanvasGeneration: vi.fn(),
  default: vi.fn()
}))

vi.mock('@/services/apiKeys', () => ({
  apiKeysService: {
    getAPIKeys: vi.fn().mockResolvedValue({ api_keys: [] })
  }
}))

vi.mock('@/services/canvas', () => ({
  canvasService: {
    getModelCatalog: vi.fn().mockResolvedValue({ text: [], image: [], video: [] }),
    uploadVideo: vi.fn()
  }
}))

vi.mock('@/services/upload', () => ({
  fileService: {
    uploadFile: vi.fn()
  }
}))

vi.mock('@/components/canvas/assistant/CanvasAssistant.vue', () => ({
  default: {
    name: 'CanvasAssistant',
    props: ['documentId', 'selectedItemIds'],
    template: '<div class="assistant-stub"></div>'
  }
}))

describe('CanvasEditor assistant wiring', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('passes the current document id and selected item ids to the assistant rail', async () => {
    const selectedItem = ref({
      id: 'item-1',
      item_type: 'text',
      title: '文本节点 1',
      position_x: 20,
      position_y: 30,
      width: 320,
      height: 220,
      z_index: 1,
      content: { text: 'hello', promptTokens: [] },
      generation_config: {},
      last_run_status: 'idle',
      last_run_error: null,
      last_output: {},
      has_detail: true,
      is_persisted: true
    })

    useCanvasEditor.mockReturnValue({
      loading: ref(false),
      saving: ref(false),
      document: ref({ id: 'doc-1', title: 'Canvas Doc' }),
      items: ref([selectedItem.value]),
      connections: ref([]),
      selectedItemId: ref('item-1'),
      selectedItem,
      zoom: ref(1),
      pan: ref({ x: 0, y: 0 }),
      dirty: ref(false),
      loadDocument: vi.fn(),
      save: vi.fn(),
      createItem: vi.fn(),
      updateItem: vi.fn(),
      removeItem: vi.fn(),
      setSelection: vi.fn(),
      clearSelection: vi.fn(),
      startConnection: vi.fn(),
      completeConnection: vi.fn(),
      removeConnection: vi.fn(),
      updateViewport: vi.fn()
    })

    useCanvasGeneration.mockReturnValue({
      generationLoadingByItem: {},
      generationHistories: {},
      historyLoadingByItem: {},
      loadHistory: vi.fn(),
      generate: vi.fn(),
      applyGeneration: vi.fn()
    })

    const wrapper = mount(CanvasEditor, {
      global: {
        directives: {
          loading: {
            mounted() {},
            updated() {}
          }
        },
        stubs: {
          CanvasConnectionActions: true,
          CanvasGenerationHistoryDrawer: true,
          CanvasImageStudio: true,
          CanvasLinkCreateMenu: true,
          CanvasLinkDragOverlay: true,
          CanvasWorkbenchLayout: {
            name: 'CanvasWorkbenchLayout',
            template: '<div class="workbench-stub"><slot /></div>'
          },
          CanvasTextStudio: true,
          CanvasVideoStudio: true,
          KonvaCanvasStage: true
        }
      }
    })

    const assistant = wrapper.findComponent({ name: 'CanvasAssistant' })
    expect(assistant.exists()).toBe(true)
    expect(assistant.props('documentId')).toBe('doc-1')
    expect(assistant.props('selectedItemIds')).toEqual(['item-1'])

    selectedItem.value = null
    await nextTick()

    expect(assistant.props('selectedItemIds')).toEqual([])
  })
})
