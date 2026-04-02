import { describe, expect, it } from 'vitest'
import { buildCanvasHistoryEntries } from '@/utils/canvasGenerationHistory'

describe('buildCanvasHistoryEntries', () => {
  it('filters out failed generations from the visible history list', () => {
    const entries = buildCanvasHistoryEntries({
      item: {
        item_type: 'image',
        content: {
          result_image_object_key: 'history/success.png'
        }
      },
      mediaType: 'image',
      histories: [
        {
          id: 'generation-failed',
          status: 'failed',
          created_at: '2026-04-02T10:00:00Z',
          request_payload: {
            prompt_plain_text: 'failed prompt'
          },
          result_payload: {
            result_image_url: 'https://cdn.example.com/failed.png'
          }
        },
        {
          id: 'generation-success',
          status: 'completed',
          created_at: '2026-04-02T11:00:00Z',
          request_payload: {
            prompt_plain_text: 'success prompt',
            model: 'gpt-image-1'
          },
          result_payload: {
            result_image_object_key: 'history/success.png',
            result_image_url: 'https://cdn.example.com/success.png'
          }
        }
      ]
    })

    expect(entries).toHaveLength(1)
    expect(entries[0]).toMatchObject({
      id: 'generation-success',
      prompt: 'success prompt',
      model: 'gpt-image-1',
      isActive: true
    })
  })
})
