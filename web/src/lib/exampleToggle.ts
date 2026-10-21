const STORAGE_KEY = 'overcount.showExample'

/** Whether the example + diagram block is open. Open unless the learner closed it before. */
export function loadShowExample(): boolean {
  try {
    return localStorage.getItem(STORAGE_KEY) !== 'false'
  } catch {
    return true
  }
}

/** Remembers the choice across problems and visits. */
export function saveShowExample(show: boolean): void {
  try {
    localStorage.setItem(STORAGE_KEY, String(show))
  } catch {
    // Storage can be unavailable (private mode); the toggle still works for this page.
  }
}
