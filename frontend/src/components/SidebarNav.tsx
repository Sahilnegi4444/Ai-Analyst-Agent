import React, { useState } from "react";
import {
  Plus,
  Home,
  MessageSquare,
  Search,
  PanelLeftClose,
  PanelLeftOpen,
  Trash2,
} from "lucide-react";

export interface Session {
  id: string;
  title: string;
  updatedAt?: string;
}

interface SidebarNavProps {
  sessions?: Session[];
  activeSessionId?: string | null;
  onSelectSession?: (id: string) => void;
  onNewChat?: () => void;
  onDeleteSession?: (id: string) => void;
}

export const SidebarNav: React.FC<SidebarNavProps> = ({
  sessions = [],
  activeSessionId,
  onSelectSession,
  onNewChat,
  onDeleteSession,
}) => {
  const [collapsed, setCollapsed] = useState<boolean>(false);

  if (collapsed) {
    return (
      <aside className="icon-rail">
        <button
          type="button"
          className="rail-icon-btn"
          title="Expand sidebar"
          onClick={() => setCollapsed(false)}
        >
          <PanelLeftOpen size={18} />
        </button>
        <div style={{ width: "24px", height: "1px", backgroundColor: "#e2e8f0", margin: "4px 0" }} />
        <button
          type="button"
          className="rail-icon-btn"
          title="New Chat"
          onClick={onNewChat}
        >
          <Plus size={18} />
        </button>
        <button
          type="button"
          className="rail-icon-btn"
          title="Home"
        >
          <Home size={18} />
        </button>
      </aside>
    );
  }

  return (
    <aside className="sidebar flex flex-col justify-between h-full bg-slate-50 border-r border-slate-200">
      <div>
        {/* Sidebar Header */}
        <div className="sidebar-header flex items-center justify-between p-4 border-b border-slate-200">
          <div className="flex items-center gap-2">
            <div className="logo-badge">R</div>
            <span className="sidebar-title">RAG Chat</span>
          </div>
          <button
            type="button"
            className="rail-icon-btn"
            title="Collapse sidebar"
            onClick={() => setCollapsed(true)}
          >
            <PanelLeftClose size={18} />
          </button>
        </div>

        {/* Action Button */}
        <div className="p-3">
          <button
            type="button"
            className="new-chat-btn"
            onClick={onNewChat}
          >
            <Plus size={16} />
            <span>New chat</span>
          </button>
        </div>

        {/* Navigation Items */}
        <div className="px-3">
          <div className="nav-item active">
            <Home size={16} />
            <span>Home</span>
          </div>
        </div>

        {/* Chat History Section */}
        <div className="chats-section">
          <div className="chats-header flex items-center justify-between px-3 py-2">
            <span className="chats-title">Chats</span>
            <Search size={14} className="search-icon" />
          </div>

          <div className="sessions-list">
            {sessions.length === 0 ? (
              <div className="empty-sessions-hint">No previous chats</div>
            ) : (
              sessions.map((sess) => (
                <div
                  key={sess.id}
                  className={`chat-history-item ${activeSessionId === sess.id ? "active" : ""}`}
                  onClick={() => onSelectSession && onSelectSession(sess.id)}
                >
                  <MessageSquare size={14} className="chat-icon" />
                  <span className="chat-history-label">{sess.title || "Untitled Session"}</span>
                  {onDeleteSession && (
                    <button
                      type="button"
                      className="session-delete-btn"
                      title="Delete chat"
                      onClick={(e) => {
                        e.stopPropagation();
                        onDeleteSession(sess.id);
                      }}
                    >
                      <Trash2 size={12} />
                    </button>
                  )}
                </div>
              ))
            )}
          </div>
        </div>
      </div>
    </aside>
  );
};

export default SidebarNav;
