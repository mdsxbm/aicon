/**
 * @vitest-environment jsdom
 */

import { beforeEach, describe, expect, it, vi } from 'vitest'

const encoder = new TextEncoder()

const createStreamResponse = (chunks, headers = {}) => {
  const queue = chunks.map((chunk) => encoder.encode(chunk))
  return {
    ok: true,
    status: 200,
    headers: {
      get: (name) => headers[String(name || '').toLowerCase()] || ''
    },
    body: {
      getReader: () => ({
        read: vi.fn(async () => {
          if (!queue.length) {
            return { done: true, value: undefined }
          }
          return { done: false, value: queue.shift() }
        }),
        releaseLock: vi.fn()
      })
    }
  }
}

describe('canvas assistant service', () => {
  beforeEach(() => {
    vi.resetModules()
    vi.clearAllMocks()
    global.fetch = vi.fn()
  })

  it('normalizes new agent protocol events from chat', async () => {
    global.fetch.mockResolvedValueOnce(
      createStreamResponse([
        'data: {"type":"agent.session.started","data":{"session_id":"session-1"}}\n\n',
        'data: {"type":"agent.step.started","data":{"id":"step-1","title":"Plan turn","status":"running"}}\n\n',
        'data: {"type":"agent.tool.call","data":{"id":"tool-1","tool_name":"canvas.update_items","args":{"updates":[{"item_id":"item-1"}]}}}\n\n',
        'data: {"type":"agent.interrupt.requested","data":{"session_id":"session-1","interrupt_id":"interrupt-1","kind":"confirm_execute","title":"确认执行","message":"请选择后继续","actions":["approve","reject"],"scope_item_ids":["item-1"]}}\n\n',
        'data: {"type":"agent.done","data":{"session_id":"session-1"}}\n\n'
      ])
    )

    const { canvasAssistantService } = await import('@/services/canvasAssistant')

    const events = []
    await canvasAssistantService.chat(
      {
        documentId: 'doc-1',
        message: '更新这个节点',
        selectedItemIds: ['item-1']
      },
      {
        onEvent: (event) => events.push(event)
      }
    )

    expect(JSON.parse(global.fetch.mock.calls[0][1].body)).toEqual({
      document_id: 'doc-1',
      message: '更新这个节点',
      selected_item_ids: ['item-1']
    })
    expect(events[0]).toMatchObject({ kind: 'session', sessionId: 'session-1' })
    expect(events[1]).toMatchObject({
      kind: 'step',
      step: { id: 'step-1', title: 'Plan turn', status: 'running' }
    })
    expect(events[2]).toMatchObject({
      kind: 'tool',
      toolCall: { id: 'tool-1', toolName: 'canvas.update_items' }
    })
    expect(events[3]).toMatchObject({
      kind: 'interrupt',
      interrupt: {
        interruptId: 'interrupt-1',
        kind: 'confirm_execute',
        scopeItemIds: ['item-1']
      }
    })
    expect(events[4]).toMatchObject({ kind: 'done' })
  })

  it('posts resume payloads using interrupt decision fields', async () => {
    global.fetch.mockResolvedValueOnce(createStreamResponse(['data: {"type":"agent.done","data":{"session_id":"session-1"}}\n\n']))

    const { canvasAssistantService } = await import('@/services/canvasAssistant')

    await canvasAssistantService.resume({
      documentId: 'doc-1',
      sessionId: 'session-1',
      interruptId: 'interrupt-1',
      decision: 'approve',
      selectedModelId: 'model-a',
      selectedItemIds: ['item-1']
    })

    expect(JSON.parse(global.fetch.mock.calls[0][1].body)).toEqual({
      document_id: 'doc-1',
      session_id: 'session-1',
      interrupt_id: 'interrupt-1',
      decision: 'approve',
      selected_model_id: 'model-a',
      selected_item_ids: ['item-1']
    })
  })
})
