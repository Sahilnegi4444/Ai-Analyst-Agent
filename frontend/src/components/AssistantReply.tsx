import React, { useState } from "react";
import { Copy, RotateCcw, ThumbsUp, ThumbsDown, ChevronDown, ChevronUp, Layers } from "lucide-react";
import ContextCards, { type ContextChunk } from "./ContextCards";

interface AssistantReplyProps {
  content: string;
  reasoning?: string;
  contextChunks?: ContextChunk[];
  isStreaming?: boolean;
}

export const AssistantReply: React.FC<AssistantReplyProps> = ({
  content,
  reasoning,
  contextChunks = [],
  isStreaming = false,
}) => {
  const [copied, setCopied] = useState<boolean>(false);
  const [showReasoning, setShowReasoning] = useState<boolean>(false);

  const handleCopy = () => {
    navigator.clipboard.writeText(content);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="assistant-reply-container" style={{ width: "100%", display: "flex", flexDirection: "column", gap: "12px" }}>
      {/* Reasoning / Thinking Accordion */}
      {reasoning && (
        <div 
          style={{
            borderRadius: "8px",
            border: "1px solid #e2e8f0",
            backgroundColor: "#f8fafc",
            padding: "8px 12px",
            fontSize: "13px",
            color: "#475569",
          }}
        >
          <div 
            onClick={() => setShowReasoning(!showReasoning)}
            style={{ display: "flex", alignItems: "center", justifyContent: "space-between", cursor: "pointer" }}
          >
            <span style={{ fontWeight: 500, display: "flex", alignItems: "center", gap: "6px" }}>
              🧠 Thought Process / Reasoning
            </span>
            {showReasoning ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
          </div>
          {showReasoning && (
            <div style={{ marginTop: "8px", paddingTop: "8px", borderTop: "1px solid #e2e8f0", fontSize: "12px", whiteSpace: "pre-wrap", color: "#64748b" }}>
              {reasoning}
            </div>
          )}
        </div>
      )}

      {/* Main Content Markdown */}
      <div className="assistant-message-content" style={{ fontSize: "14px", lineHeight: "1.6", color: "#1e293b", whiteSpace: "pre-wrap" }}>
        {content}
        {isStreaming && <span className="streaming-cursor">▌</span>}
      </div>

      {/* Action Icons Bar & Sources indicator */}
      {!isStreaming && (
        <div style={{ display: "flex", alignItems: "center", gap: "12px", marginTop: "4px" }}>
          <button
            type="button"
            onClick={handleCopy}
            title="Copy response"
            style={{ background: "none", border: "none", color: "#94a3b8", cursor: "pointer", display: "flex", alignItems: "center", gap: "4px", fontSize: "12px" }}
          >
            <Copy size={14} />
            {copied && <span style={{ color: "#10b981" }}>Copied</span>}
          </button>
          
          <button
            type="button"
            title="Retry"
            style={{ background: "none", border: "none", color: "#94a3b8", cursor: "pointer", display: "flex", alignItems: "center" }}
          >
            <RotateCcw size={14} />
          </button>
          
          <button
            type="button"
            title="Helpful"
            style={{ background: "none", border: "none", color: "#94a3b8", cursor: "pointer", display: "flex", alignItems: "center" }}
          >
            <ThumbsUp size={14} />
          </button>

          <button
            type="button"
            title="Not helpful"
            style={{ background: "none", border: "none", color: "#94a3b8", cursor: "pointer", display: "flex", alignItems: "center" }}
          >
            <ThumbsDown size={14} />
          </button>

          {contextChunks.length > 0 && (
            <div className="source-counter-pill" style={{ marginLeft: "auto", display: "flex", alignItems: "center", gap: "4px", fontSize: "12px", color: "#2563eb", backgroundColor: "#eff6ff", padding: "2px 8px", borderRadius: "12px" }}>
              <Layers size={12} />
              <span>{contextChunks.length} sources</span>
            </div>
          )}
        </div>
      )}

      {/* Context Cards Section */}
      {contextChunks.length > 0 && (
        <ContextCards chunks={contextChunks} />
      )}
    </div>
  );
};

export default AssistantReply;
