import React, { useState } from "react";
import { FileText, ChevronDown, ChevronUp, ExternalLink } from "lucide-react";

export interface ContextChunk {
  title: string;
  chars?: string;
  body: string;
  source?: string;
  badge?: string;
  tone?: string;
  score?: number;
}

interface ContextCardsProps {
  chunks?: ContextChunk[];
  headerLabel?: string;
}

export const ContextCards: React.FC<ContextCardsProps> = ({
  chunks = [],
  headerLabel = "Retrieved Context",
}) => {
  const [expanded, setExpanded] = useState<boolean>(true);

  if (!chunks || chunks.length === 0) return null;

  return (
    <div className="retrieved-context-container">
      {/* Header bar */}
      <div 
        className="retrieved-context-header"
        onClick={() => setExpanded(!expanded)}
        style={{ cursor: "pointer", display: "flex", alignItems: "center", justifyContent: "space-between" }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
          <span style={{ fontSize: "13px", fontWeight: 600, color: "#334155" }}>
            {headerLabel}
          </span>
          <span className="retrieved-count-badge">{chunks.length}</span>
        </div>
        <button 
          type="button"
          style={{ background: "none", border: "none", color: "#64748b", cursor: "pointer", display: "flex", alignItems: "center" }}
        >
          {expanded ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
        </button>
      </div>

      {/* Cards list */}
      {expanded && (
        <div className="retrieved-cards-list" style={{ marginTop: "8px", display: "flex", flexDirection: "column", gap: "10px" }}>
          {chunks.map((chunk, idx) => (
            <div key={idx} className="retrieved-card">
              <div className="card-top-row">
                <div className="card-section-title">
                  <FileText size={14} style={{ color: "#64748b" }} />
                  <span>{chunk.title}</span>
                </div>
                {chunk.chars && (
                  <span className="card-char-count">{chunk.chars}</span>
                )}
              </div>

              <p className="card-body-snippet">
                {chunk.body}
              </p>

              {chunk.source && (
                <div style={{ marginTop: "8px", display: "flex", alignItems: "center", gap: "8px" }}>
                  <span className="source-tag-badge">
                    {chunk.source}
                    <ExternalLink size={10} style={{ marginLeft: "4px" }} />
                  </span>
                  {chunk.score !== undefined && (
                    <span style={{ fontSize: "11px", color: "#94a3b8" }}>
                      Score: {(chunk.score * 100).toFixed(0)}%
                    </span>
                  )}
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default ContextCards;
