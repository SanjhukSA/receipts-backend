import client from './client.js'

/**
 * List receipts with pagination.
 * @param {object} params
 * @param {number} params.page
 * @param {number} params.per_page
 * @param {string} params.sort_by
 * @param {string} params.order
 */
export async function listReceipts({ page = 1, per_page = 10, sort_by = 'created_at', order = 'desc' } = {}) {
  const { data } = await client.get('/receipts', { params: { page, per_page, sort_by, order } })
  return data
}

/**
 * Get a single receipt by id.
 * @param {string|number} id
 */
export async function getReceipt(id) {
  const { data } = await client.get(`/receipts/${id}`)
  return data
}

/**
 * Upload a receipt image.
 * @param {File} file
 * @param {function} onProgress
 */
export async function uploadReceipt(file, onProgress) {
  const form = new FormData()
  form.append('file', file)
  const { data } = await client.post('/receipts/upload', form, {
    headers: { 'Content-Type': 'multipart/form-data' },
    onUploadProgress: (e) => {
      if (onProgress && e.total) onProgress(Math.round((e.loaded * 100) / e.total))
    },
  })
  return data
}

/**
 * Process (OCR) an uploaded receipt.
 * @param {string} uploadId
 */
export async function processReceipt(uploadId) {
  const { data } = await client.post(`/receipts/${uploadId}/process`)
  return data
}

/**
 * Save a confirmed receipt.
 * @param {object} payload - ReceiptCreate body
 */
export async function saveReceipt(payload) {
  const { data } = await client.post('/receipts', payload)
  return data
}
