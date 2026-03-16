const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:8080/api'
const API_ORIGIN = new URL(API_BASE).origin

export function toAbsoluteMediaUrl(url) {
  if (!url) return ''
  if (url.startsWith('http://') || url.startsWith('https://')) return url
  if (url.startsWith('/')) return `${API_ORIGIN}${url}`
  return `${API_ORIGIN}/${url}`
}

export function resolvePlaceImage(place) {
  if (!place) return ''
  const primary = place.images?.find((img) => img?.is_primary)
  const raw = place.image_url || place.primary_image || primary?.image_url || place.images?.[0]?.image_url || ''
  return toAbsoluteMediaUrl(raw)
}
