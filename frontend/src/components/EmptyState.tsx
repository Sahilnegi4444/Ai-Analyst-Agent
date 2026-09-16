import React from "react";
import { Sparkles, Database, FileCode } from "lucide-react";

interface EmptyStateProps {
  onSelectPrompt?: (prompt: string) => void;
}

export const EmptyState: React.FC<EmptyStateProps> = ({ onSelectPrompt }) => {
  const suggestions = [
    {
      icon: <Database size={16} className="text-blue-500" />,
      title: "Query Database Schema",
      desc: "Find supplier records, order history, or workload summary",
      prompt: "Show me supplier records and active orders from the database",
    },
    {
      icon: <Sparkles size={16} className="text-amber-500" />,
      title: "RAG & Document Search",
      desc: "Search legal provisions, Bharatiya Nyaya Sanhita (BNS), or SOPs",
      prompt: "What are the punishments for offences under Chapter II?",
    },
    {
      icon: <FileCode size={16} className="text-purple-500" />,
      title: "Workload & Restock Analysis",
      desc: "Analyze restock limits or batch processing tasks",
      prompt: "Generate a restock report for low-stock supplier inventory",
    },
  ];

  return (
    <div className="welcome-container">
      <div className="welcome-avatar-gpt">
        <Sparkles size={28} />
      </div>

      <h2 className="greeting-text">
        AI Analyst & RAG Assistant
      </h2>
      <p className="welcome-subtitle">
        Ask questions about your database schemas, legal documents, or automated analytical workflows.
      </p>

      <div className="suggest-grid">
        {suggestions.map((item) => (
          <button
            key={item.title}
            type="button"
            onClick={() => onSelectPrompt?.(item.prompt)}
            className="suggest-card"
          >
            <div style={{ display: "flex", alignItems: "center", gap: "8px", marginBottom: "6px" }}>
              {item.icon}
              <span className="suggest-card-title">{item.title}</span>
            </div>
            <p className="suggest-card-desc" style={{ margin: 0 }}>{item.desc}</p>
          </button>
        ))}
      </div>
    </div>
  );
};

export default EmptyState;
