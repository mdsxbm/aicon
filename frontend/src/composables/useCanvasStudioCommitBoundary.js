import { onBeforeUnmount, onMounted, ref } from 'vue'

export function useCanvasStudioCommitBoundary(rootRef, onCommit) {
  const rootContainsFocus = ref(false)
  const suppressOutsideCommit = ref(false)
  let suppressOutsideCommitTimer = null

  const isNodeInsideRoot = (node) => Boolean(node && rootRef.value?.contains(node))
  const ignoredOverlaySelector = [
    '.el-popper',
    '.el-select-dropdown',
    '.el-dropdown__popper',
    '.el-dropdown-menu',
    '.el-overlay',
    '.el-overlay-dialog',
    '.el-dialog',
    '.el-drawer'
  ].join(', ')
  const isIgnoredOverlayTarget = (node) => Boolean(
    node &&
    typeof node.closest === 'function' &&
    node.closest(ignoredOverlaySelector)
  )

  const flushCommit = () => {
    if (!rootContainsFocus.value) {
      return
    }

    rootContainsFocus.value = false
    onCommit?.()
  }

  const handleRootPointerDown = () => {
    suppressOutsideCommit.value = true
    if (suppressOutsideCommitTimer) {
      clearTimeout(suppressOutsideCommitTimer)
    }
    suppressOutsideCommitTimer = setTimeout(() => {
      suppressOutsideCommit.value = false
      suppressOutsideCommitTimer = null
    }, 0)
  }

  const handleRootFocusIn = () => {
    rootContainsFocus.value = true
  }

  const handleDocumentFocusIn = (event) => {
    if (isNodeInsideRoot(event.target)) {
      rootContainsFocus.value = true
      return
    }

    if (suppressOutsideCommit.value || isIgnoredOverlayTarget(event.target)) {
      return
    }

    flushCommit()
  }

  const handleDocumentPointerDown = (event) => {
    if (isNodeInsideRoot(event.target) || isIgnoredOverlayTarget(event.target)) {
      return
    }

    flushCommit()
  }

  onMounted(() => {
    if (typeof document === 'undefined') {
      return
    }

    document.addEventListener('focusin', handleDocumentFocusIn, true)
    document.addEventListener('pointerdown', handleDocumentPointerDown, true)
  })

  onBeforeUnmount(() => {
    if (typeof document !== 'undefined') {
      document.removeEventListener('focusin', handleDocumentFocusIn, true)
      document.removeEventListener('pointerdown', handleDocumentPointerDown, true)
    }

    if (suppressOutsideCommitTimer) {
      clearTimeout(suppressOutsideCommitTimer)
      suppressOutsideCommitTimer = null
    }

    rootContainsFocus.value = false
  })

  return {
    handleRootPointerDown,
    handleRootFocusIn,
    flushCommit
  }
}
