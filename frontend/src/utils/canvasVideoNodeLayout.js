const DEFAULT_VIDEO_NODE_BOUNDS = {
  maxWidth: 360,
  maxHeight: 420,
  minWidth: 180,
  minHeight: 180
}

function toPositiveNumber(value) {
  const numeric = Number(value)
  return Number.isFinite(numeric) && numeric > 0 ? numeric : 0
}

function parseAspectRatioString(aspectRatio) {
  const normalized = String(aspectRatio || '').trim()
  if (!normalized) {
    return 0
  }

  const [widthPart, heightPart] = normalized.split(':')
  const width = toPositiveNumber(widthPart)
  const height = toPositiveNumber(heightPart)
  if (!width || !height) {
    return 0
  }

  return width / height
}

function clampVideoSize(width, height, bounds) {
  const safeBounds = {
    ...DEFAULT_VIDEO_NODE_BOUNDS,
    ...(bounds || {})
  }

  let nextWidth = Math.max(toPositiveNumber(width), safeBounds.minWidth)
  let nextHeight = Math.max(toPositiveNumber(height), safeBounds.minHeight)
  const aspectRatio = nextWidth / Math.max(nextHeight, 1e-6)

  const fitScale = Math.min(
    safeBounds.maxWidth / nextWidth,
    safeBounds.maxHeight / nextHeight,
    1
  )
  nextWidth *= fitScale
  nextHeight *= fitScale

  if (nextWidth < safeBounds.minWidth) {
    nextWidth = safeBounds.minWidth
    nextHeight = nextWidth / Math.max(aspectRatio, 1e-6)
  }
  if (nextHeight < safeBounds.minHeight) {
    nextHeight = safeBounds.minHeight
    nextWidth = nextHeight * aspectRatio
  }

  const finalScale = Math.min(
    safeBounds.maxWidth / nextWidth,
    safeBounds.maxHeight / nextHeight,
    1
  )

  return {
    width: Math.round(nextWidth * finalScale),
    height: Math.round(nextHeight * finalScale)
  }
}

function resolveConfiguredAspectRatio(item) {
  return parseAspectRatioString(
    item?.generation_config?.aspectRatio ||
      item?.content?.generationConfig?.aspectRatio ||
      item?.content?.lastGenerationRequest?.generationConfig?.aspectRatio ||
      item?.config?.aspect_ratio ||
      ''
  )
}

export function resolveCanvasVideoAspectRatio(item, videoMeta) {
  const metaWidth = toPositiveNumber(videoMeta?.videoWidth || videoMeta?.naturalWidth)
  const metaHeight = toPositiveNumber(videoMeta?.videoHeight || videoMeta?.naturalHeight)
  if (metaWidth && metaHeight) {
    return metaWidth / metaHeight
  }

  const configuredRatio = resolveConfiguredAspectRatio(item)
  if (configuredRatio) {
    return configuredRatio
  }

  const itemWidth = toPositiveNumber(item?.width)
  const itemHeight = toPositiveNumber(item?.height)
  if (itemWidth && itemHeight) {
    return itemWidth / itemHeight
  }

  return 16 / 9
}

export function resolveCanvasVideoNodeSize(item, videoMeta, bounds) {
  const metaWidth = toPositiveNumber(videoMeta?.videoWidth || videoMeta?.naturalWidth)
  const metaHeight = toPositiveNumber(videoMeta?.videoHeight || videoMeta?.naturalHeight)
  if (metaWidth && metaHeight) {
    return clampVideoSize(metaWidth, metaHeight, bounds)
  }

  const aspectRatio = resolveCanvasVideoAspectRatio(item, videoMeta)
  return clampVideoSize(aspectRatio * 240, 240, bounds)
}
