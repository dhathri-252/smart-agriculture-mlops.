/** Catalogue utility tests (node:test) — no React/DOM needed. */
import { test } from 'node:test'
import assert from 'node:assert/strict'
import {
  displayName, filterCatalogue, matchesSearch, normalizeLang, LANG_STORAGE_KEY,
} from './catalogueUtils.js'

const rice = {
  id: 'rice', name_en: 'Rice',
  names: { en: 'Rice', te: 'వరి', hi: 'धान' },
  name_status: { en: 'verified', te: 'unverified', hi: 'unverified' },
  categories: ['cereals_millets'], model_supported: true,
}
const tomato = {
  id: 'tomato', name_en: 'Tomato',
  names: { en: 'Tomato', te: 'టమాటా' },
  name_status: { en: 'verified', te: 'unverified' },
  categories: ['vegetables'], model_supported: false,
}
const items = [rice, tomato]

test('category filtering keeps only matching crops', () => {
  const out = filterCatalogue(items, { category: 'vegetables' })
  assert.deepEqual(out.map((c) => c.id), ['tomato'])
})

test('crop selection by id (detail lookup)', () => {
  const found = items.find((c) => c.id === 'rice')
  assert.equal(found.name_en, 'Rice')
})

test('multilingual search matches English + Telugu + Hindi names', () => {
  assert.equal(matchesSearch(rice, 'rice'), true)
  assert.equal(matchesSearch(rice, 'వరి'), true)
  assert.equal(matchesSearch(rice, 'धान'), true)
  assert.equal(matchesSearch(rice, 'zzz'), false)
})

test('language persistence key + normalization', () => {
  assert.equal(LANG_STORAGE_KEY, 'sa_language')
  assert.equal(normalizeLang('te'), 'te')
  assert.equal(normalizeLang('bn'), 'bn')
  assert.equal(normalizeLang('xx'), 'en')
})

test('missing translation falls back to English with flag', () => {
  const got = displayName(tomato, 'bn') // tomato has no bn name
  assert.equal(got.text, 'Tomato')
  assert.equal(got.missing, true)
  const ok = displayName(rice, 'te')
  assert.equal(ok.text, 'వరి')
  assert.equal(ok.unverified, true)
})

test('model-only filter separates predictions from guides', () => {
  const out = filterCatalogue(items, { modelOnly: true })
  assert.deepEqual(out.map((c) => c.id), ['rice'])
})
