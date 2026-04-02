const resolveGenerationPreviewUrl = (generation, mediaType) => {
  const payload = generation?.result_payload || {}
  if (mediaType === 'video') {
    return String(payload.result_video_url || '').trim()
  }
  return String(payload.result_image_url || '').trim()
}

const resolveGenerationPromptText = (generation) =>
  String(
    generation?.request_payload?.prompt_plain_text ||
      generation?.request_payload?.prompt ||
      generation?.request_payload?.prompt_text ||
      ''
  ).trim()

const formatHistoryTime = (value) => {
  if (!value) return ''
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) {
    return ''
  }
  return date.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  })
}

const isHistoryGenerationActive = (item, generation, mediaType) => {
  const payload = generation?.result_payload || {}
  const content = item?.content || {}
  if (mediaType === 'video') {
    const currentObjectKey = String(
      content.result_video_object_key || ''
    ).trim()
    const generationObjectKey = String(
      payload.result_video_object_key || ''
    ).trim()
    if (currentObjectKey && generationObjectKey) {
      return currentObjectKey === generationObjectKey
    }
    return (
      String(content.result_video_url || '').trim() ===
      String(payload.result_video_url || '').trim()
    )
  }

  const currentObjectKey = String(content.result_image_object_key || '').trim()
  const generationObjectKey = String(
    payload.result_image_object_key || ''
  ).trim()
  if (currentObjectKey && generationObjectKey) {
    return currentObjectKey === generationObjectKey
  }
  return (
    String(content.result_image_url || '').trim() ===
    String(payload.result_image_url || '').trim()
  )
}

export const buildCanvasHistoryEntries = ({
  item = null,
  mediaType = 'image',
  histories = []
} = {}) =>
  histories
    .filter(
      (entry) =>
        String(entry?.status || '')
          .trim()
          .toLowerCase() !== 'failed'
    )
    .map((entry) => ({
      ...entry,
      previewUrl: resolveGenerationPreviewUrl(entry, mediaType),
      prompt: resolveGenerationPromptText(entry),
      model: String(entry?.request_payload?.model || '').trim(),
      createdAtText: formatHistoryTime(entry?.created_at),
      statusText: entry?.status === 'completed' ? '已完成' : '处理中',
      isActive: item ? isHistoryGenerationActive(item, entry, mediaType) : false
    }))
