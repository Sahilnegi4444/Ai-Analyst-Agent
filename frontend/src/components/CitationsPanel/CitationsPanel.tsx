import React from 'react'
import { BookOpen, FileText, ChevronDown, ChevronRight } from 'lucide-react'

export interface Source {
  filename: string
  title: string
  content_snippet: string
  confidence: number
}

interface CitationsPanelProps {
  messageId: string
  sources: Source[]
  activeCitation: string | null
  setActiveCitation: (id: string | null) => void
}

export const CitationsPanel: React.FC<CitationsPanelProps> = ({
  messageId,
  sources,
  activeCitation,
  setActiveCitation
}) => {
  if (!sources || sources.length === 0) {
    return null
  }

  return (
    <div className="citations-panel" role="region" aria-label="Reference citations panel">
      <span className="citations-panel-heading">
        <BookOpen size={12} aria-hidden="true" />
        <span>Retrieved Document Sources</span>
      </span>
      <div className="citations-list" role="list">
        {sources.map((src, idx) => {
          const cardId = `${messageId}-src-${idx}`
          const isExpanded = activeCitation === cardId
          return (
            <div key={idx} className="citation-card" role="listitem">
              <button
                className="citation-card-header"
                onClick={() => setActiveCitation(isExpanded ? null : cardId)}
                aria-expanded={isExpanded}
                aria-controls={`citation-body-${cardId}`}
                aria-label={`Source file ${src.filename}, Match Confidence: ${Math.round(src.confidence * 100)}%`}
              >
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <FileText size={13} style={{ color: 'var(--accent-brand)' }} aria-hidden="true" />
                  <span className="citation-filename">{src.filename}</span>
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <span className="citation-match-badge">
                    Match: {Math.round(src.confidence * 100)}%
                  </span>
                  {isExpanded ? (
                    <ChevronDown size={13} aria-hidden="true" />
                  ) : (
                    <ChevronRight size={13} aria-hidden="true" />
                  )}
                </div>
              </button>
              {isExpanded && (
                <div
                  id={`citation-body-${cardId}`}
                  className="citation-card-body"
                  role="region"
                  aria-label={`Snippet from ${src.filename}`}
                >
                  <p className="citation-snippet-text">{src.content_snippet}</p>
                </div>
              )}
            </div>
          )
        })}
      </div>
    </div>
  )
}
