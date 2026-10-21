import { beforeEach, describe, expect, it, vi } from 'vitest'
import { loadShowExample, saveShowExample } from './exampleToggle'

describe('example toggle', () => {
  beforeEach(() => {
    // Tests run in Node, which has no localStorage: use a small in-memory stand-in.
    const store = new Map<string, string>()
    vi.stubGlobal('localStorage', {
      getItem: (key: string) => store.get(key) ?? null,
      setItem: (key: string, value: string) => store.set(key, value),
    })
  })

  it('is open by default', () => {
    expect(loadShowExample()).toBe(true)
  })

  it('remembers a closed toggle for the next problem', () => {
    saveShowExample(false)
    expect(loadShowExample()).toBe(false)
    saveShowExample(true)
    expect(loadShowExample()).toBe(true)
  })
})
