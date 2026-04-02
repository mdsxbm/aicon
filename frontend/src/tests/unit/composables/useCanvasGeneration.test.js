/**
 * @vitest-environment jsdom
 */

import { createApp, defineComponent } from 'vue'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { useCanvasGeneration } from '@/composables/useCanvasGeneration'
import { canvasService } from '@/services/canvas'

vi.mock('@/services/canvas', () => ({
  canvasService: {
    listGenerations: vi.fn(),
    applyGeneration: vi.fn(),
    generateTextStream: vi.fn(),
    generateImageStream: vi.fn(),
    generateVideoStream: vi.fn()
  }
}))

const mountComposable = (updateItem, getItemById = () => null) => {
  let composable = null
  const root = document.createElement('div')
  const app = createApp(
    defineComponent({
      setup() {
        composable = useCanvasGeneration(updateItem, getItemById)
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

const buildSseResponse = (events) => {
  const encoder = new TextEncoder()
  const chunks = events.map(({ event, data }) => {
    return `event: ${event}\ndata: ${JSON.stringify(data)}\n\n`
  })
  let index = 0

  return {
    ok: true,
    body: {
      getReader() {
        return {
          read: vi.fn().mockImplementation(async () => {
            if (index < chunks.length) {
              const value = encoder.encode(chunks[index])
              index += 1
              return { done: false, value }
            }
            return { done: true, value: undefined }
          })
        }
      }
    }
  }
}

describe('useCanvasGeneration SSE handling', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('keeps a video task alive through a transient fail event until completion', async () => {
    const updateItem = vi.fn()
    const { app, composable } = mountComposable(updateItem)

    const response = buildSseResponse([
      { event: 'start', data: { status: 'processing' } },
      {
        event: 'progress',
        data: {
          status: 'processing',
          provider_task_id: 'provider-task-1',
          generation_id: 'generation-1',
          provider_payload: { stage: 'polling' }
        }
      },
      {
        event: 'fail',
        data: {
          status: 'processing',
          transient_status_issue: true,
          error_message: 'temporary status fetch issue',
          provider_payload: { stage: 'polling' }
        }
      },
      {
        event: 'complete',
        data: {
          status: 'completed',
          item: {
            content: {
              result_video_url: 'https://cdn.example.com/video.mp4',
              result_video_object_key: 'uploads/video.mp4'
            },
            generation_config: { model: 'veo_3_1-fast' },
            last_run_status: 'completed',
            last_output: { result_video_object_key: 'uploads/video.mp4' }
          },
          generation: {
            id: 'generation-1',
            result_payload: { result_video_object_key: 'uploads/video.mp4' }
          }
        }
      }
    ])

    canvasService.generateVideoStream.mockResolvedValue(response)

    const item = {
      id: 'item-1',
      item_type: 'video',
      content: { prompt: 'Create a cinematic push-in' },
      generation_config: { model: 'veo_3_1-fast' }
    }

    await expect(composable.generate(item, {})).resolves.toMatchObject({
      message: '视频生成完成',
      generation: {
        id: 'generation-1'
      }
    })

    expect(updateItem).toHaveBeenCalledWith(
      'item-1',
      expect.objectContaining({
        last_run_status: 'processing',
        last_run_error: null
      }),
      { persist: false }
    )

    expect(updateItem).toHaveBeenCalledWith(
      'item-1',
      expect.objectContaining({
        last_run_status: 'completed',
        last_run_error: null,
        is_persisted: true
      })
    )

    expect(
      updateItem.mock.calls.some((call) => call[1].last_run_status === 'failed')
    ).toBe(false)

    app.unmount()
  })

  it('keeps transient media urls in local completed image results for immediate preview', async () => {
    const updateItem = vi.fn()
    const { app, composable } = mountComposable(updateItem)

    const response = buildSseResponse([
      { event: 'start', data: { status: 'processing' } },
      {
        event: 'complete',
        data: {
          status: 'completed',
          item: {
            content: {
              result_image_object_key: 'uploads/generated.png',
              result_image_url: 'https://cdn.example.com/uploads/generated.png'
            },
            generation_config: { model: 'gpt-image-1' },
            last_run_status: 'completed',
            last_output: {
              result_image_object_key: 'uploads/generated.png',
              result_image_url: 'https://cdn.example.com/uploads/generated.png'
            }
          },
          generation: {
            id: 'generation-image-1',
            result_payload: {
              result_image_object_key: 'uploads/generated.png',
              result_image_url: 'https://cdn.example.com/uploads/generated.png'
            }
          }
        }
      }
    ])

    canvasService.generateImageStream.mockResolvedValue(response)

    const item = {
      id: 'item-image-1',
      item_type: 'image',
      content: { prompt: 'White studio desk' },
      generation_config: { model: 'gpt-image-1' }
    }

    await composable.generate(item, {})

    expect(updateItem).toHaveBeenCalledWith(
      'item-image-1',
      expect.objectContaining({
        content: {
          result_image_object_key: 'uploads/generated.png',
          result_image_url: 'https://cdn.example.com/uploads/generated.png'
        },
        last_output: {
          result_image_object_key: 'uploads/generated.png',
          result_image_url: 'https://cdn.example.com/uploads/generated.png'
        },
        last_run_status: 'completed'
      })
    )

    app.unmount()
  })

  it('applies a selected image history entry and reloads item history', async () => {
    const updateItem = vi.fn()
    const { app, composable } = mountComposable(updateItem)

    canvasService.applyGeneration.mockResolvedValue({
      item: {
        content: {
          result_image_object_key: 'history/selected-image.png',
          result_image_url: 'https://cdn.example.com/history/selected-image.png'
        },
        generation_config: { model: 'gpt-image-1' },
        last_run_status: 'completed',
        last_run_error: null,
        last_output: {
          result_image_object_key: 'history/selected-image.png',
          result_image_url: 'https://cdn.example.com/history/selected-image.png'
        }
      }
    })
    canvasService.listGenerations.mockResolvedValue({
      generations: [
        {
          id: 'generation-image-2',
          result_payload: {
            result_image_url:
              'https://cdn.example.com/history/selected-image.png'
          }
        }
      ]
    })

    const response = await composable.applyGeneration(
      'item-image-1',
      'generation-image-2'
    )

    expect(canvasService.applyGeneration).toHaveBeenCalledWith(
      'item-image-1',
      'generation-image-2'
    )
    expect(updateItem).toHaveBeenCalledWith(
      'item-image-1',
      expect.objectContaining({
        content: {
          result_image_object_key: 'history/selected-image.png',
          result_image_url: 'https://cdn.example.com/history/selected-image.png'
        },
        last_run_status: 'completed',
        last_run_error: null,
        is_persisted: true
      })
    )
    expect(canvasService.listGenerations).toHaveBeenCalledWith('item-image-1', {
      page: 1,
      size: 20
    })
    expect(composable.generationHistories['item-image-1']).toEqual([
      {
        id: 'generation-image-2',
        result_payload: {
          result_image_url: 'https://cdn.example.com/history/selected-image.png'
        }
      }
    ])
    expect(response).toEqual(
      expect.objectContaining({
        item: expect.objectContaining({
          last_run_status: 'completed'
        })
      })
    )

    app.unmount()
  })

  it('preserves existing prompt metadata when applying a history entry with partial content', async () => {
    const updateItem = vi.fn()
    const currentItem = {
      id: 'item-image-1',
      item_type: 'image',
      content: {
        prompt: 'white studio desk',
        promptPlainText: 'white studio desk',
        promptTokens: [{ type: 'text', text: 'white studio desk' }],
        style_reference_image_object_key: 'reference/style.png'
      },
      generation_config: {
        model: 'gpt-image-1',
        api_key_id: 'key-1'
      }
    }
    const { app, composable } = mountComposable(
      updateItem,
      (itemId) => (itemId === currentItem.id ? currentItem : null)
    )

    canvasService.applyGeneration.mockResolvedValue({
      item: {
        content: {
          result_image_object_key: 'history/selected-image.png',
          result_image_url: 'https://cdn.example.com/history/selected-image.png'
        },
        generation_config: { model: 'gpt-image-1' },
        last_run_status: 'completed',
        last_run_error: null,
        last_output: {
          result_image_object_key: 'history/selected-image.png',
          result_image_url: 'https://cdn.example.com/history/selected-image.png'
        }
      }
    })
    canvasService.listGenerations.mockResolvedValue({ generations: [] })

    await composable.applyGeneration('item-image-1', 'generation-image-2')

    expect(updateItem).toHaveBeenCalledWith(
      'item-image-1',
      expect.objectContaining({
        content: {
          prompt: 'white studio desk',
          promptPlainText: 'white studio desk',
          promptTokens: [{ type: 'text', text: 'white studio desk' }],
          style_reference_image_object_key: 'reference/style.png',
          result_image_object_key: 'history/selected-image.png',
          result_image_url: 'https://cdn.example.com/history/selected-image.png'
        },
        generation_config: {
          model: 'gpt-image-1',
          api_key_id: 'key-1'
        }
      })
    )

    app.unmount()
  })
})
