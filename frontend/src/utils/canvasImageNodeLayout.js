const DEFAULT_IMAGE_NODE_BOUNDS = {
  maxWidth: 360,
  maxHeight: 420,
  minWidth: 180,
  minHeight: 140
}

function toPositiveNumber(value) {
  const numeric = Number(value)
  return Number.isFinite(numeric) && numeric > 0 ? numeric : 0
}

function parseAspectRatioString(aspectRatio) {
  const normalized = String(aspectRatio || '').trim()
  const [widthPart, heightPart] = normalized.split(':')
  const width = toPositiveNumber(widthPart)
  const height = toPositiveNumber(heightPart)
  if (!width || !height) {
    return 0
  }
  return width / height
}

function clampImageSize(width, height, bounds) {
  const safeBounds = {
    ...DEFAULT_IMAGE_NODE_BOUNDS,
    ...(bounds || {})
  }

  let nextWidth = Math.max(toPositiveNumber(width), safeBounds.minWidth)
  let nextHeight = Math.max(toPositiveNumber(height), safeBounds.minHeight)
  const aspectRatio = nextWidth / nextHeight

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

export function resolveCanvasImageAspectRatio(item, imageMeta) {
  const metaWidth = toPositiveNumber(imageMeta?.naturalWidth)
  const metaHeight = toPositiveNumber(imageMeta?.naturalHeight)
  if (metaWidth && metaHeight) {
    return metaWidth / metaHeight
  }

  const itemWidth = toPositiveNumber(item?.width)
  const itemHeight = toPositiveNumber(item?.height)
  if (itemWidth && itemHeight) {
    return itemWidth / itemHeight
  }

  const configuredRatio = parseAspectRatioString(
    item?.generation_config?.aspectRatio || item?.config?.aspect_ratio
  )
  return configuredRatio || 1
}

export function resolveCanvasImageNodeSize(item, imageMeta, bounds) {
  const metaWidth = toPositiveNumber(imageMeta?.naturalWidth)
  const metaHeight = toPositiveNumber(imageMeta?.naturalHeight)
  if (metaWidth && metaHeight) {
    return clampImageSize(metaWidth, metaHeight, bounds)
  }

  const aspectRatio = resolveCanvasImageAspectRatio(item, imageMeta)
  return clampImageSize(aspectRatio * 300, 300, bounds)
}
