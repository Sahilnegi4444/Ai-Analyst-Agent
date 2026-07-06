import React from 'react'
import { Send, Info } from 'lucide-react'

interface ChatInputProps {
  input: string
  setInput: (val: string) => void
  loading: boolean
  onSubmit: (query: string) => void
}

export const ChatInput: React.FC<ChatInputProps> = ({
  input,
  setInput,
  loading,
  onSubmit
}) => {
  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (!input.trim() || loading) return
    onSubmit(input)
  }

  return (
    <div className="input-area-wrapper">
      <form onSubmit={handleSubmit} className="input-container" role="search" aria-label="Submit database queries">
        {/* Hidden accessible label for screen readers */}
        <label htmlFor="chat-query-input" className="sr-only" style={{ display: 'none' }}>
          Query input text field
        </label>
        <input
          id="chat-query-input"
          type="text"
          className="input-field"
          placeholder="Query sales databases or fetch policies..."
          value={input}
          onChange={(e) => setInput(e.target.value)}
          disabled={loading}
          autoComplete="off"
        />
        <button
          type="submit"
          className="send-btn"
          disabled={loading || !input.trim()}
          aria-label="Send Query"
        >
          <Send size={16} aria-hidden="true" />
        </button>
      </form>
      <div className="disclaimer-text">
        <Info size={11} style={{ verticalAlign: 'middle', marginRight: '4px', display: 'inline-block' }} aria-hidden="true" />
        Antigravity SQL Sandbox environment compiles safe read-only queries with caching enabled.
      </div>
    </div>
  )
}
