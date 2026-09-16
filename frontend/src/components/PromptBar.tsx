import React, { useState, type KeyboardEvent, type FormEvent } from "react";
import { ArrowUp, Paperclip } from "lucide-react";

interface PromptBarProps {
  onSend: (text: string) => void;
  disabled?: boolean;
  placeholder?: string;
}

export const PromptBar: React.FC<PromptBarProps> = ({
  onSend,
  disabled = false,
  placeholder = "Ask anything...",
}) => {
  const [draft, setDraft] = useState<string>("");

  const canSend = draft.trim().length > 0 && !disabled;

  const submit = () => {
    if (!canSend) return;
    onSend(draft.trim());
    setDraft("");
  };

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      submit();
    }
  };

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault();
    submit();
  };

  return (
    <form onSubmit={handleSubmit} className="w-full">
      <div className="prompt-bar-wrapper" style={{
        position: "relative",
        display: "flex",
        alignItems: "center",
        backgroundColor: "#ffffff",
        border: "1px solid #e2e8f0",
        borderRadius: "24px",
        padding: "8px 14px",
        boxShadow: "0 2px 8px rgba(0, 0, 0, 0.05)",
        transition: "border-color 0.15s ease",
      }}>
        <textarea
          value={draft}
          onChange={(e) => setDraft(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder={placeholder}
          rows={1}
          disabled={disabled}
          style={{
            flex: 1,
            border: "none",
            outline: "none",
            resize: "none",
            fontSize: "14px",
            color: "#1e293b",
            backgroundColor: "transparent",
            fontFamily: "inherit",
            maxHeight: "120px",
            padding: "4px 0",
          }}
        />

        <div style={{ display: "flex", alignItems: "center", gap: "8px", marginLeft: "8px" }}>
          <button
            type="button"
            style={{
              background: "none",
              border: "none",
              color: "#94a3b8",
              cursor: "pointer",
              display: "flex",
              alignItems: "center",
              padding: "4px",
            }}
            title="Attach file"
          >
            <Paperclip size={18} />
          </button>
          
          <button
            type="submit"
            disabled={!canSend}
            style={{
              backgroundColor: canSend ? "#0f172a" : "#f1f5f9",
              color: canSend ? "#ffffff" : "#94a3b8",
              border: "none",
              borderRadius: "50%",
              width: "32px",
              height: "32px",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              cursor: canSend ? "pointer" : "not-allowed",
              transition: "all 0.15s ease",
            }}
          >
            <ArrowUp size={16} />
          </button>
        </div>
      </div>
    </form>
  );
};

export default PromptBar;
