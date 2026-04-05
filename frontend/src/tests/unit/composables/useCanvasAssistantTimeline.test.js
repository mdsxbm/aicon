/**
 * @vitest-environment jsdom
 */

import { describe, expect, it } from 'vitest'
import { buildCanvasAssistantTimelineItems } from '@/composables/useCanvasAssistantTimeline'

describe('useCanvasAssistantTimeline', () => {
  it('keeps messages, activity items, interrupt cards and errors in order', () => {
    const items = buildCanvasAssistantTimelineItems({
      messages: [
        { id: 'm-1', role: 'user', content: '更新一下', order: 1 },
        { id: 'm-2', role: 'assistant', content: '已完成', order: 4 }
      ],
      stepEvents: [
        { id: 'step-1', title: 'Plan turn', status: 'completed', order: 2 }
      ],
      toolTrace: [
        { id: 'tool-1', toolName: 'canvas.update_items', status: 'completed', order: 3, result: { updated: 1 } }
      ],
      pendingInterrupt: {
        interruptId: 'interrupt-1',
        kind: 'confirm_execute',
        title: '确认执行',
        order: 5
      },
      error: 'stream closed unexpectedly'
    })

    expect(items.map((item) => item.type)).toEqual([
      'user_message',
      'activity',
      'activity',
      'assistant_message',
      'interrupt_card',
      'error_notice'
    ])
    expect(items[1]).toMatchObject({
      type: 'activity',
      activity: { id: 'step-1', activityType: 'step' }
    })
    expect(items[2]).toMatchObject({
      type: 'activity',
      activity: { id: 'tool-1', activityType: 'tool', toolName: 'canvas.update_items' }
    })
  })
})
