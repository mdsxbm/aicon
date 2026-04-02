import { onBeforeUnmount, reactive } from 'vue'
import { canvasService } from '@/services/canvas'

const POLL_INTERVAL_MS = 2500

const applyGenerationResultToContent = (itemType, currentContent = {}, resultPayload = {}) => {
  const nextContent = { ...currentContent }
  if (itemType === 'text' && resultPayload.text) {
    nextContent.text = resultPayload.text
  }
  if (itemType === 'image' && resultPayload.result_image_url) {
    nextContent.result_image_url = resultPayload.result_image_url
  }
  if (itemType === 'video' && resultPayload.result_video_url) {
    nextContent.result_video_url = resultPayload.result_video_url
  }
  if (resultPayload.provider_task_id) {
    nextContent.provider_task_id = resultPayload.provider_task_id
  }
  if (resultPayload.task_id) {
    nextContent.task_id = resultPayload.task_id
  }
  return nextContent
}

export function useCanvasGeneration(updateItem) {
  const state = reactive({
    loadingByItem: {},
    histories: {},
    historyLoadingByItem: {},
    pollingTimersByItem: {},
    pollingByItem: {}
  })

  const clearPolling = (itemId) => {
    const timer = state.pollingTimersByItem[itemId]
    if (timer) {
      window.clearTimeout(timer)
      delete state.pollingTimersByItem[itemId]
    }
    delete state.pollingByItem[itemId]
  }

  const setLoading = (itemId, value) => {
    state.loadingByItem[itemId] = value
  }

  const loadHistory = async (itemId) => {
    state.historyLoadingByItem[itemId] = true
    try {
      const response = await canvasService.listGenerations(itemId, { page: 1, size: 20 })
      state.histories[itemId] = response.generations || []
      return state.histories[itemId]
    } catch {
      state.histories[itemId] = []
      return state.histories[itemId]
    } finally {
      state.historyLoadingByItem[itemId] = false
    }
  }

  const syncItemFromGeneration = (item, generation) => {
    updateItem(item.id, {
      content: applyGenerationResultToContent(item.item_type, item.content, generation.result_payload || {}),
      last_run_status: generation.status,
      last_run_error: generation.error_message || null,
      last_output: generation.result_payload || {},
      is_persisted: true
    })
  }

  const pollGeneration = async (item, generationId) => {
    clearPolling(item.id)
    state.pollingByItem[item.id] = true

    const tick = async () => {
      try {
        const history = await loadHistory(item.id)
        const generation = history.find((entry) => entry.id === generationId)
        if (!generation) {
          state.pollingTimersByItem[item.id] = window.setTimeout(tick, POLL_INTERVAL_MS)
          return
        }

        syncItemFromGeneration(item, generation)

        if (['completed', 'failed'].includes(generation.status)) {
          clearPolling(item.id)
          setLoading(item.id, false)
          return
        }

        state.pollingTimersByItem[item.id] = window.setTimeout(tick, POLL_INTERVAL_MS)
      } catch {
        state.pollingTimersByItem[item.id] = window.setTimeout(tick, POLL_INTERVAL_MS)
      }
    }

    state.pollingTimersByItem[item.id] = window.setTimeout(tick, POLL_INTERVAL_MS)
  }

  const generate = async (item, payload = {}) => {
    setLoading(item.id, true)
    try {
      let response
      if (item.item_type === 'text') {
        response = await canvasService.generateText(item.id, payload)
      } else if (item.item_type === 'image') {
        response = await canvasService.generateImage(item.id, payload)
      } else {
        response = await canvasService.generateVideo(item.id, payload)
      }

      updateItem(item.id, {
        content: {
          ...item.content,
          task_id: response.generation?.result_payload?.task_id || item.content?.task_id
        },
        generation_config: response.item.generation_config,
        last_run_status: response.item.last_run_status,
        last_run_error: response.item.last_run_error,
        last_output: response.item.last_output,
        is_persisted: true
      })
      state.histories[item.id] = [
        response.generation,
        ...(state.histories[item.id] || []).filter((entry) => entry.id !== response.generation.id)
      ]
      await pollGeneration(item, response.generation.id)
      return response
    } catch (error) {
      setLoading(item.id, false)
      throw error
    }
  }

  const applyGeneration = async (itemId, generationId) => {
    const response = await canvasService.applyGeneration(itemId, generationId)
    updateItem(itemId, {
      content: response.item.content,
      generation_config: response.item.generation_config,
      last_run_status: response.item.last_run_status,
      last_run_error: response.item.last_run_error,
      last_output: response.item.last_output,
      is_persisted: true
    })
    await loadHistory(itemId)
    return response
  }

  onBeforeUnmount(() => {
    Object.keys(state.pollingTimersByItem).forEach(clearPolling)
  })

  return {
    generationLoadingByItem: state.loadingByItem,
    generationHistories: state.histories,
    historyLoadingByItem: state.historyLoadingByItem,
    generationPollingByItem: state.pollingByItem,
    loadHistory,
    generate,
    applyGeneration,
    clearPolling
  }
}
