export function buildPromptDerivatives(tokens = []) {
  const chipMap = new Map()
  const promptPlainText = tokens
    .map((token) => {
      if (token.type === 'mention') {
        const mapKey = `${token.nodeType}:${token.nodeId}`
        const currentChip = chipMap.get(mapKey) || {
          nodeId: token.nodeId,
          nodeType: token.nodeType,
          title: token.nodeTitleSnapshot || '',
          count: 0
        }

        currentChip.count += 1
        if (!currentChip.title && token.nodeTitleSnapshot) {
          currentChip.title = token.nodeTitleSnapshot
        }
        chipMap.set(mapKey, currentChip)
        return `@${token.nodeTitleSnapshot || ''}`
      }

      return token.text || ''
    })
    .join('')

  return {
    promptPlainText,
    chips: Array.from(chipMap.values())
  }
}

export function removeMentionsByNodeId(tokens = [], nodeId = '') {
  return tokens.filter((token) => !(token.type === 'mention' && token.nodeId === nodeId))
}
