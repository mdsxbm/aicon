function stripRichText(value = '') {
  let html = String(value || '').replace(/<\/?(div|p|h[1-6]|br|li)[^>]*>/gi, '\n')
  html = html.replace(/<[^>]+>/g, '')
  html = html.replace(/&nbsp;/g, ' ')
  html = html.replace(/\n\s*\n/g, '\n')
  return html.trim()
}

export const resolveCanvasTextPreview = (item) =>
  stripRichText(item?.content?.text || item?.content?.text_preview || item?.content?.prompt || '')

export const resolveCanvasStageMediaUrl = (item) => {
  if (!item) {
    return ''
  }
  if (item.item_type === 'image') {
    return String(item.content?.result_image_url || item.content?.reference_image_url || '').trim()
  }
  if (item.item_type === 'video') {
    return String(item.content?.result_video_url || '').trim()
  }
  return ''
}

const defaultTranslate = (_key, fallback) => fallback

export const isCanvasStageItemGenerating = (item) => {
  const status = String(item?.last_run_status || '').trim().toLowerCase()
  return ['pending', 'processing', 'running'].includes(status)
}

export const resolveCanvasStageGeneratingMeta = (item, t = defaultTranslate) => {
  if (!isCanvasStageItemGenerating(item)) {
    return null
  }

  if (item.item_type === 'image') {
    return {
      label: t('canvas.image_generating_label', 'AI 正在生成图像'),
      hint: t('canvas.image_generating_hint', '预计 30 秒至 2 分钟')
    }
  }

  if (item.item_type === 'video') {
    return {
      label: t('canvas.video_generating_label', 'AI 正在生成视频'),
      hint: t('canvas.video_generating_hint', '预计 2 至 10 分钟')
    }
  }

  return null
}

export const resolveCanvasStagePreviewText = (item, t = defaultTranslate) => {
  if (!item) {
    return ''
  }

  if (item.item_type === 'text') {
    return resolveCanvasTextPreview(item)
  }

  if (item.item_type === 'image') {
    if (resolveCanvasStageMediaUrl(item)) {
      return ''
    }
    return t('canvas.image_result_pending', '等待图片结果')
  }

  if (item.item_type === 'video') {
    if (resolveCanvasStageMediaUrl(item)) {
      return t('canvas.video_stage_generated', '已生成视频结果')
    }
    return String(item?.last_run_error || '').trim() || t('canvas.video_result_pending', '等待视频内容')
  }

  return ''
}

export const resolveStageVideoPreviewTargets = ({ items = [], editingItemId = '' } = {}) =>
  items.filter((item) => item?.item_type === 'video' && String(item.id || '') !== String(editingItemId || ''))

export const releaseCanvasStageVideoEntry = (entry) => {
  const video = entry?.video
  if (!video) {
    return
  }

  video.onloadeddata = null
  video.onseeked = null
  video.onerror = null
  video.onloadedmetadata = null
  video.pause?.()
  if (typeof video.removeAttribute === 'function') {
    video.removeAttribute('src')
  } else if ('src' in video) {
    video.src = ''
  }
  video.load?.()
}
