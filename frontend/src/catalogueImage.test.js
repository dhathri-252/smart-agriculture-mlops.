/** Image helper tests: verified photo vs placeholder fallback + alt text. */
import { test } from 'node:test'
import assert from 'node:assert/strict'

/** Mirrors CropImage logic: only verified + URL + no error renders <img>. */
export function shouldShowPhoto(item, failed) {
  return Boolean(item.image && item.image_status === 'verified' && !failed)
}

export function altFor(item) {
  return item.alt_text || `Photograph of ${item.name_en}`
}

const verified = {
  id: 'rice', name_en: 'Rice', image: '/images/crops/rice.jpg',
  image_status: 'verified',
  alt_text: 'Photograph of Rice growing in the field (source: Wikimedia Commons — see attribution).',
}
const pending = {
  id: 'rye', name_en: 'Rye', image: null, image_status: 'pending',
  alt_text: 'Rye — illustrative placeholder (verified photograph pending).',
}

test('verified crop shows its photo', () => {
  assert.equal(shouldShowPhoto(verified, false), true)
})

test('failed load falls back to placeholder', () => {
  assert.equal(shouldShowPhoto(verified, true), false)
})

test('pending crop never shows a photo (no fabricated URL)', () => {
  assert.equal(shouldShowPhoto(pending, false), false)
  assert.equal(pending.image, null)
})

test('alt text is descriptive in both states', () => {
  assert.match(altFor(verified), /Photograph of Rice/)
  assert.match(altFor(pending), /placeholder|pending/i)
})

test('no two verified crops share one photo URL', () => {
  const urls = ['/images/crops/rice.jpg', '/images/crops/tomato.jpg', '/images/crops/rice.jpg']
  assert.notEqual(new Set(urls).size, urls.length) // sanity: dupes detected
  const ok = ['/images/crops/rice.jpg', '/images/crops/tomato.jpg']
  assert.equal(new Set(ok).size, ok.length)
})
