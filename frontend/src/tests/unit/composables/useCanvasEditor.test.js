/**
 * @vitest-environment jsdom
 */

import { createApp, defineComponent, nextTick } from 'vue'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { useCanvasEditor } from '@/composables/useCanvasEditor'
import { canvasService } from '@/services/canvas'

vi.mock('@/services/canvas', () => ({
  canvasService: {
    getLite: vi.fn(),
    getItem: vi.fn(),
    updateItem: vi.fn(),
    createItem: vi.fn(),
    deleteItem: vi.fn(),
    deleteItems: vi.fn(),
    createConnection: vi.fn(),
    deleteConnection: vi.fn()
  }
}))

const mountComposable = () => {
  let composable = null
  const root = document.createElement('div')
  const app = createApp(
    defineComponent({
      setup() {
        composable = useCanvasEditor()
        return () => null
      }
    })
  )
  app.mount(root)
  return {
    app,
    get composable() {
      return composable
    }
  }
}

describe('useCanvasEditor item merging', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('replaces last_output so stale video errors do not survive a later success', async () => {
    canvasService.getLite.mockResolvedValue({
      document: { id: 'doc-1', title: 'Canvas' },
      items: [
        {
          id: 'item-1',
          item_type: 'video',
          title: '视频节点 1',
          position_x: 10,
          position_y: 20,
          width: 360,
          height: 300,
          z_index: 1,
          content: { prompt: 'foo' },
          generation_config: {},
          last_run_status: 'failed',
          last_run_error: 'old failure',
          last_output: {
            transient_status_issue: true,
            status_fetch_error: 'temporary status failure'
          }
        }
      ],
      connections: []
    })

    const { app, composable } = mountComposable()
    await composable.loadDocument('doc-1')
    await nextTick()

    composable.updateItem('item-1', {
      last_run_status: 'completed',
      last_run_error: null,
      last_output: {
        result_video_object_key: 'uploads/final.mp4'
      }
    }, { persist: false })

    expect(composable.items.value[0].last_run_status).toBe('completed')
    expect(composable.items.value[0].last_run_error).toBeNull()
    expect(composable.items.value[0].last_output).toEqual({
      result_video_object_key: 'uploads/final.mp4'
    })

    app.unmount()
  })

  it('batch deletes selected items with a single request and removes linked connections locally', async () => {
    canvasService.getLite.mockResolvedValue({
      document: { id: 'doc-1', title: 'Canvas' },
      items: [
        {
          id: 'item-1',
          item_type: 'text',
          title: '文本节点 1',
          position_x: 10,
          position_y: 20,
          width: 320,
          height: 220,
          z_index: 1,
          content: {},
          generation_config: {},
          last_output: {}
        },
        {
          id: 'item-2',
          item_type: 'image',
          title: '图片节点 1',
          position_x: 360,
          position_y: 20,
          width: 340,
          height: 280,
          z_index: 2,
          content: {},
          generation_config: {},
          last_output: {}
        },
        {
          id: 'item-3',
          item_type: 'video',
          title: '视频节点 1',
          position_x: 720,
          position_y: 20,
          width: 360,
          height: 300,
          z_index: 3,
          content: {},
          generation_config: {},
          last_output: {}
        }
      ],
      connections: [
        {
          id: 'conn-1',
          source_item_id: 'item-1',
          target_item_id: 'item-2',
          source_handle: 'right',
          target_handle: 'left'
        },
        {
          id: 'conn-2',
          source_item_id: 'item-2',
          target_item_id: 'item-3',
          source_handle: 'right',
          target_handle: 'left'
        }
      ]
    })
    canvasService.getItem.mockResolvedValue({
      id: 'item-1',
      item_type: 'text',
      title: '文本节点 1',
      position_x: 10,
      position_y: 20,
      width: 320,
      height: 220,
      z_index: 1,
      content: {},
      generation_config: {},
      last_output: {}
    })

    const { app, composable } = mountComposable()
    await composable.loadDocument('doc-1')
    await nextTick()

    composable.setSelections(['item-1', 'item-2'])
    await composable.removeItems(['item-1', 'item-2'])

    expect(canvasService.deleteItems).toHaveBeenCalledTimes(1)
    expect(canvasService.deleteItems).toHaveBeenCalledWith('doc-1', ['item-1', 'item-2'])
    expect(composable.items.value.map((item) => item.id)).toEqual(['item-3'])
    expect(composable.connections.value).toEqual([])
    expect(composable.selectedItemIds.value).toEqual([])
    expect(composable.selectedItem.value).toBeNull()

    app.unmount()
  })

  it('applies initial image or video generation defaults when creating a node', async () => {
    canvasService.createItem.mockResolvedValue({
      id: 'item-9',
      item_type: 'image',
      title: '图片节点 1',
      position_x: 120,
      position_y: 120,
      width: 340,
      height: 280,
      z_index: 1,
      content: { prompt: '', promptTokens: [] },
      generation_config: {
        api_key_id: 'key-1',
        model: 'image-model-1'
      },
      last_run_status: 'idle',
      last_run_error: null,
      last_output: {}
    })
    canvasService.getLite.mockResolvedValue({
      document: { id: 'doc-1', title: 'Canvas' },
      items: [],
      connections: []
    })

    const { app, composable } = mountComposable()
    await composable.loadDocument('doc-1')
    await nextTick()

    await composable.createItem('image', {
      generation_config: {
        api_key_id: 'key-1',
        model: 'image-model-1'
      }
    })

    expect(canvasService.createItem).toHaveBeenCalledWith(
      'doc-1',
      expect.objectContaining({
        generation_config: {
          api_key_id: 'key-1',
          model: 'image-model-1'
        }
      })
    )

    app.unmount()
  })
})
