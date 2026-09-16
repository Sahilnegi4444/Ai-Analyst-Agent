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
    <div style={{ display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", height: "100%", padding: "20px", textAlign: "center" }}>
      <div style={{
        width: "56px",
        height: "56px",
        borderRadius: "16px",
        backgroundColor: "#f1f5f9",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        marginBottom: "16px",
      }}>
        <Sparkles size={28} style={{ color: "#3b82f6" }} />
      </div>

      <h2 style={{ fontSize: "20px", fontWeight: 600, color: "#0f172a", marginBottom: "8px" }}>
        AI Analyst & RAG Assistant
      </h2>
      <p style={{ fontSize: "14px", color: "#64748b", maxWidth: "460px", marginBottom: "28px" }}>
        Ask questions about your database schemas, legal documents, or automated analytical workflows.
      </p>

      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(240px, 1fr))", gap: "12px", width: "100%", maxWidth: "780px" }}>
        {suggestions.map((item, idx) => (
          <div
            key={idx}
            onClick={() => onSelectPrompt && onSelectPrompt(item.prompt)}
            style={{
              padding: "16px",
              borderRadius: "12px",
              border: "1px solid #e2e8f0",
              backgroundColor: "#ffffff",
              textAlign: "left",
              cursor: "pointer",
              transition: "all 0.15s ease",
              boxShadow: "0 1px 3px rgba(0,0,0,0.02)",
            }}
            className="suggestion-card hover:border-slate-300 hover:shadow-md"
          >
            <div style={{ display: "flex", alignItems: "center", gap: "8px", marginBottom: "6px" }}>
              {item.icon}
              <span style={{ fontSize: "13px", fontWeight: 600, color: "#1e293b" }}>{item.title}</span>
            </div>
            <p style={{ fontSize: "12px", color: "#64748b", margin: 0 }}>{item.desc}</p>
          </div>
        ))}
      </div>
    </div>
  );
};

export default EmptyState;
