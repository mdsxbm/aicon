import { describe, it, expect } from 'vitest'
import { resolveCanvasRunErrorSummary, resolveCanvasRunStatusMeta, resolveCanvasTextPreview, resolveCanvasStagePreviewText } from '@/utils/canvasStageMedia'

describe('canvasStageMedia rich text preview', () => {
  it('preserves rich text structure in the text preview summary', () => {
    const preview = resolveCanvasTextPreview({
      content: {
        text: '<h1>Title</h1><p>First paragraph</p><ul><li>Alpha</li><li>Beta</li></ul>'
      }
    })

    expect(preview).toContain('Title')
    expect(preview).toContain('First paragraph')
    expect(preview).toContain('• Alpha')
    expect(preview).toContain('• Beta')
  })

  it('keeps plain text previews readable', () => {
    const preview = resolveCanvasStagePreviewText({
      item_type: 'text',
      content: {
        text: 'Plain text content'
      }
    })

    expect(preview).toBe('Plain text content')
  })

  it('returns retrying status meta for transient video status fetch failures', () => {
    const meta = resolveCanvasRunStatusMeta({
      item_type: 'video',
      last_run_status: 'processing',
      last_output: {
        transient_status_issue: true,
        status_fetch_error: 'temporary status failure'
      }
    })

    expect(meta).toMatchObject({
      tone: 'warning',
      label: '状态同步中'
    })
  })

  it('uses status detail as video preview fallback text', () => {
    const preview = resolveCanvasStagePreviewText({
      item_type: 'video',
      last_run_status: 'pending',
      content: {}
    })

    expect(preview).toBe('任务已入队，正在等待执行。')
  })

  it('compresses raw json-like errors into a readable summary', () => {
    const summary = resolveCanvasRunErrorSummary('{"code":"","message":"生成过程中出现异常，请重新发起请求"}')

    expect(summary).toBe('生成过程中出现异常，请重试。')
  })
})
