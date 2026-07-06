import { Database, Clock, Zap, Sparkles } from 'lucide-react'
import { SqlResultsWidget } from '../SqlResultsWidget/SqlResultsWidget'
import { CitationsPanel } from '../CitationsPanel/CitationsPanel'
import type { Source } from '../CitationsPanel/CitationsPanel'

export interface Message {
  id: string
  sender: 'user' | 'agent'
  text: string
  intent?: string
  sql_generated?: string | null
  sql_results?: Record<string, unknown>[] | null
  sources?: Source[] | null
  latency_seconds?: number
  cached?: boolean
  status?: string
}

interface MessageItemProps {
  msg: Message
  activeCitation: string | null
  setActiveCitation: (id: string | null) => void
}

// Helper to format text/bullets
const renderFormattedText = (text: string) => {
  if (!text) return null;
  const lines = text.split('\n');
  return lines.map((line, idx) => {
    let cleanLine = line;
    let isBullet = false;
    const bulletMatch = cleanLine.match(/^(\s*)[*\-•]\s+(.*)/);
    if (bulletMatch) {
      isBullet = true;
      cleanLine = bulletMatch[2];
    }
    cleanLine = cleanLine.replace(/^#+\s+/, '');
    const parts = cleanLine.split(/\*\*([^*]+)\*\*/g);
    const formattedLine = parts.map((part, i) => {
      if (i % 2 === 1) {
        return <strong key={i} className="bold-text">{part}</strong>;
      }
      return part;
    });

    if (isBullet) {
      return (
        <div key={idx} className="bullet-item">
          <span className="bullet-dot" aria-hidden="true">•</span>
          <span className="bullet-content">{formattedLine}</span>
        </div>
      );
    }

    return (
      <p key={idx} className="text-paragraph">
        {formattedLine}
      </p>
    );
  });
};

export const MessageItem: React.FC<MessageItemProps> = ({
  msg,
  activeCitation,
  setActiveCitation
}) => {
  return (
    <div className={`chat-message-wrapper ${msg.sender}`} role="log" aria-label={`Message from ${msg.sender}`}>
      <div className={`message-bubble-container ${msg.sender}`}>
        <div className="message-sender-identity">
          {msg.sender === 'user' ? 'You' : 'AI Agent'}
        </div>
        <div className={`message-bubble ${msg.sender}`}>
          <div className="formatted-text">{renderFormattedText(msg.text)}</div>

          {/* Dynamic database details accordion */}
          {msg.sender === 'agent' && msg.sql_generated && (
            <div className="sql-details-accordion">
              <details className="sql-details-element">
                <summary className="sql-details-summary">
                  <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                    <Database size={12} aria-hidden="true" />
                    <span>Inspect SQL Query</span>
                  </div>
                </summary>
                <div className="sql-details-content">
                  <pre className="sql-details-code">{msg.sql_generated}</pre>
                </div>
              </details>
            </div>
          )}

          {/* DYNAMIC CHARTING & TABLE WIDGET (SQL RESULTS) */}
          {msg.sender === 'agent' && msg.sql_results && (
            <SqlResultsWidget results={msg.sql_results} />
          )}

          {/* RAG CITATIONS WIDGET */}
          {msg.sender === 'agent' && msg.sources && msg.sources.length > 0 && (
            <CitationsPanel
              messageId={msg.id}
              sources={msg.sources}
              activeCitation={activeCitation}
              setActiveCitation={setActiveCitation}
            />
          )}
        </div>

        {/* METRICS & RUNTIME STATS */}
        {msg.sender === 'agent' && (msg.latency_seconds !== undefined || msg.cached !== undefined) && (
          <div className="message-metrics-bar" role="status" aria-label="Query execution stats">
            {msg.intent && (
              <span className="metrics-pill text-teal">
                <Sparkles size={10} style={{ marginRight: '4px' }} aria-hidden="true" />
                Intent: {msg.intent}
              </span>
            )}
            {msg.latency_seconds !== undefined && (
              <span className="metrics-pill">
                <Clock size={10} style={{ marginRight: '4px' }} aria-hidden="true" />
                Latency: {msg.latency_seconds.toFixed(2)}s
              </span>
            )}
            {msg.cached !== undefined && (
              <span className={`metrics-pill ${msg.cached ? 'cached-hit' : 'cached-miss'}`}>
                <Zap size={10} style={{ marginRight: '4px' }} aria-hidden="true" />
                {msg.cached ? 'Cache Hit' : 'Cache Miss'}
              </span>
            )}
          </div>
        )}
      </div>
    </div>
  )
}
