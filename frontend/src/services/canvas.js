import { del, get, patch, post, put } from './api'

export const canvasService = {
  list(params = {}) {
    return get('/canvas-documents', { params })
  },

  create(payload) {
    return post('/canvas-documents', payload)
  },

  get(documentId) {
    return get(`/canvas-documents/${documentId}`)
  },

  getLite(documentId) {
    return get(`/canvas-documents/${documentId}`, { params: { mode: 'lite' } })
  },

  update(documentId, payload) {
    return patch(`/canvas-documents/${documentId}`, payload)
  },

  remove(documentId) {
    return del(`/canvas-documents/${documentId}`)
  },

  getGraph(documentId) {
    return get(`/canvas-documents/${documentId}/graph`)
  },

  saveGraph(documentId, payload) {
    return put(`/canvas-documents/${documentId}/graph`, payload)
  },

  createItem(documentId, payload) {
    return post(`/canvas-documents/${documentId}/items`, payload)
  },

  getItem(documentId, itemId) {
    return get(`/canvas-documents/${documentId}/items/${itemId}`)
  },

  updateItem(documentId, itemId, payload) {
    return patch(`/canvas-documents/${documentId}/items/${itemId}`, payload)
  },

  deleteItem(documentId, itemId) {
    return del(`/canvas-documents/${documentId}/items/${itemId}`)
  },

  getItemPreviews(documentId, itemIds = []) {
    return post(`/canvas-documents/${documentId}/items/previews`, { item_ids: itemIds })
  },

  createConnection(documentId, payload) {
    return post(`/canvas-documents/${documentId}/connections`, payload)
  },

  deleteConnection(documentId, connectionId) {
    return del(`/canvas-documents/${documentId}/connections/${connectionId}`)
  },

  generateText(itemId, payload = {}) {
    return post(`/canvas-items/${itemId}/generate-text`, payload)
  },

  generateImage(itemId, payload = {}) {
    return post(`/canvas-items/${itemId}/generate-image`, payload)
  },

  generateVideo(itemId, payload = {}) {
    return post(`/canvas-items/${itemId}/generate-video`, payload)
  },

  listGenerations(itemId, params = {}) {
    return get(`/canvas-items/${itemId}/generations`, { params })
  },

  applyGeneration(itemId, generationId) {
    return post(`/canvas-items/${itemId}/generations/${generationId}/apply`)
  }
}

export default canvasService
