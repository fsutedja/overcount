import { useEffect, useRef } from 'react'
import { MathfieldElement } from 'mathlive'

MathfieldElement.fontsDirectory = '/mathlive/fonts'
MathfieldElement.soundsDirectory = null

/** Typing these sequences turns them into rendered math, Desmos-style. */
const SHORTCUTS = {
  choose: '\\binom{#?}{#?}',
  'C(': '\\binom{#?}{#?}',
  'P(': '\\operatorname{P}\\left(#?,#?\\right)',
  sum: '\\sum_{#?=#?}^{#?}#?',
}

const COUNTING_KEYBOARD = {
  label: 'Counting',
  rows: [
    [
      { latex: '\\binom{#@}{#?}', label: 'C(n,k)' },
      { latex: '\\operatorname{P}\\left(#@,#?\\right)', label: 'P(n,k)' },
      { latex: '#@!', label: 'n!' },
      { latex: '\\frac{#@}{#?}', label: 'a/b' },
      { latex: '#@^{#?}', label: 'xⁿ' },
      { latex: 'e', label: 'e' },
      { latex: '\\sum_{#?=#?}^{#?}#@', label: 'Σ' },
    ],
    ['7', '8', '9', '\\times', '(', ')'],
    ['4', '5', '6', '+', '-', '[left]'],
    ['1', '2', '3', '0', '[backspace]', '[right]'],
  ],
}

interface MathInputProps {
  label: string
  onChange: (latex: string) => void
  onSubmit: () => void
  invalid?: boolean
  autoFocus?: boolean
}

export function MathInput({ label, onChange, onSubmit, invalid = false, autoFocus = false }: MathInputProps) {
  const ref = useRef<MathfieldElement>(null)
  // Latest callbacks for the long-lived MathLive listeners, updated after each render.
  const callbacks = useRef({ onChange, onSubmit })
  useEffect(() => {
    callbacks.current = { onChange, onSubmit }
  })

  useEffect(() => {
    if (autoFocus) ref.current?.focus()
  }, [autoFocus])

  useEffect(() => {
    const field = ref.current
    if (!field) return
    field.inlineShortcuts = { ...field.inlineShortcuts, ...SHORTCUTS }
    field.smartFence = true
    field.mathVirtualKeyboardPolicy = 'auto'
    window.mathVirtualKeyboard.layouts = [COUNTING_KEYBOARD]

    const handleInput = () => callbacks.current.onChange(field.value)
    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === 'Enter') {
        event.preventDefault()
        callbacks.current.onSubmit()
      } else if (event.key === '*') {
        // Show a real multiplication sign instead of an asterisk.
        event.preventDefault()
        event.stopPropagation()
        field.executeCommand(['insert', '\\times'])
      }
    }
    // Capture phase: MathLive consumes Enter inside its shadow DOM before bubbling listeners run.
    field.addEventListener('input', handleInput)
    field.addEventListener('keydown', handleKeyDown, { capture: true })
    return () => {
      field.removeEventListener('input', handleInput)
      field.removeEventListener('keydown', handleKeyDown, { capture: true })
    }
  }, [])

  return (
    <math-field
      ref={ref}
      aria-label={label}
      className={`block w-full rounded-lg border-2 bg-card px-3 py-2 ${invalid ? 'border-wrong-ink' : 'border-accent'}`}
    />
  )
}
