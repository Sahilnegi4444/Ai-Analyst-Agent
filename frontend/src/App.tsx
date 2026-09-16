import React, { useState, useEffect, useRef } from 'react'
import {
  Plus,
  MessageSquare,
  Trash2,
  Database,
  BarChart2,
  BarChart3,
  PanelLeft,
  Table2,
  Paperclip,
  Sparkles,
  ChevronDown,
  ArrowUp
} from 'lucide-react'
import {
  ResponsiveContainer,
  AreaChart,
  Area,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip
} from 'recharts'
import { DocumentModal } from './components/DocumentModal'
import { AnalyticsModal } from './components/AnalyticsModal'
import './App.css'

const generateSessionId = (): string => {
  if (typeof window !== 'undefined' && window.crypto) {
    if (window.crypto.randomUUID) {
      return window.crypto.randomUUID()
    }
    const array = new Uint32Array(4)
    window.crypto.getRandomValues(array)
    return 'sess-' + Array.from(array, dec => dec.toString(36)).join('').substring(0, 16)
  }
  return 'sess-' + Date.now().toString(36) + '-' + Math.floor(Date.now() * 1000).toString(36)
}

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

// =====================================================================
// LOCALSTORAGE SESSION TITLE CACHE (PERMANENT UNTIL DELETED)
// =====================================================================
const getStoredTitles = (): Record<string, string> => {
  try {
    const data = localStorage.getItem('ai_analyst_session_titles_map')
    return data ? JSON.parse(data) : {}
  } catch {
    return {}
  }
}

const saveStoredTitle = (sid: string, title: string) => {
  try {
    const titles = getStoredTitles()
    if (!titles[sid]) { // Only save if NOT already set (lock to first prompt)
      titles[sid] = title
      localStorage.setItem('ai_analyst_session_titles_map', JSON.stringify(titles))
    }
  } catch (err) {
    console.error("Failed to save session title:", err)
  }
}

const removeStoredTitle = (sid: string) => {
  try {
    const titles = getStoredTitles()
    delete titles[sid]
    localStorage.setItem('ai_analyst_session_titles_map', JSON.stringify(titles))
  } catch (err) {
    console.error("Failed to remove session title:", err)
  }
}

// Helper to sanitize title for display
const formatSessionTitle = (sid: string, rawTitle?: string): string => {
  const storedMap = getStoredTitles()
  if (storedMap[sid]) return storedMap[sid].length > 24 ? storedMap[sid].substring(0, 22) + '...' : storedMap[sid]
  if (rawTitle && !rawTitle.startsWith('sess-')) {
    return rawTitle.length > 24 ? rawTitle.substring(0, 22) + '...' : rawTitle
  }
  return 'New Chat'
}

// =====================================================================
// TYPING INTERFACES
// =====================================================================
interface Source {
  filename: string
  title: string
  content_snippet: string
  confidence: number
}

interface Message {
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

interface ApiMessage {
  id: number
  sender: string
  text: string
  intent?: string
  sql_generated?: string | null
  sql_results?: Record<string, unknown>[] | null
  sources?: Source[] | null
  latency_seconds?: number
  cached?: boolean
  status?: string
}

interface SessionInfo {
  id: string
  title: string
}

// =====================================================================
// SQL RESULTS WIDGET COMPONENT
// =====================================================================
const SqlResultsWidget: React.FC<{ results: Record<string, unknown>[] }> = ({ results }) => {
  const firstRow = results && results.length > 0 ? results[0] : null
  const keys = firstRow ? Object.keys(firstRow) : []

  const dateKeys = keys.filter(key => {
    const name = key.toLowerCase()
    return name.includes('month') || name.includes('date') || name.includes('week') || name.includes('year')
  })

  const numericKeys = keys.filter(key => {
    if (!firstRow) return false
    const val = firstRow[key]
    const isId = key.toLowerCase().includes('id')
    const isDate = dateKeys.includes(key)
    return typeof val === 'number' && !isId && !isDate
  })

  const labelKeys = keys.filter(key => {
    const isNum = numericKeys.includes(key)
    return !isNum
  })

  const yAxisKey = numericKeys[0] || null

  const prioritizedDateKeys = [...dateKeys].sort((a, b) => {
    const order = ['date', 'week', 'month', 'year']
    const idxA = order.findIndex(term => a.toLowerCase().includes(term))
    const idxB = order.findIndex(term => b.toLowerCase().includes(term))
    return idxA - idxB
  })
  const xAxisKey = prioritizedDateKeys[0] || labelKeys[0] || null

  const canPlot = !!(yAxisKey && xAxisKey)
  const isChronological = dateKeys.length > 0
  const chartData = isChronological ? results : results.slice(0, 5)

  const [viewType, setViewType] = useState<'area' | 'bar' | 'table'>(
    canPlot ? (isChronological ? 'area' : 'bar') : 'table'
  )

  if (!results || results.length === 0) {
    return null
  }

  return (
    <div className="chart-card">
      <div className="widget-header">
        <span className="widget-title">
          {viewType === 'area' && (
            <>
              <BarChart3 size={15} />
              Visualized Trend Line
            </>
          )}
          {viewType === 'bar' && (
            <>
              <BarChart3 size={15} />
              Visualized Bar Comparison
            </>
          )}
          {viewType === 'table' && (
            <>
              <Table2 size={15} />
              Database Records ({results.length} rows)
            </>
          )}
        </span>
        <div style={{ display: 'flex', gap: '6px' }}>
          {canPlot && (
            <>
              <button
                className={`toggle-btn ${viewType === 'area' ? 'active' : ''}`}
                onClick={() => setViewType('area')}
              >
                Line
              </button>
              <button
                className={`toggle-btn ${viewType === 'bar' ? 'active' : ''}`}
                onClick={() => setViewType('bar')}
              >
                Bar
              </button>
            </>
          )}
          <button
            className={`toggle-btn ${viewType === 'table' ? 'active' : ''}`}
            onClick={() => setViewType('table')}
          >
            Table
          </button>
        </div>
      </div>

      {viewType === 'area' && yAxisKey && xAxisKey && (
        <div style={{ width: '100%', height: 240 }}>
          <ResponsiveContainer width="99%" height="100%">
            <AreaChart data={chartData} margin={{ top: 10, right: 10, left: -10, bottom: 0 }}>
              <defs>
                <linearGradient id="chartColor" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="var(--accent-gpt)" stopOpacity={0.4} />
                  <stop offset="95%" stopColor="var(--accent-gpt)" stopOpacity={0.0} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="var(--border-subtle)" />
              <XAxis dataKey={xAxisKey} tick={{ fill: 'var(--text-secondary)', fontSize: 11 }} stroke="var(--border-subtle)" />
              <YAxis tick={{ fill: 'var(--text-secondary)', fontSize: 11 }} stroke="var(--border-subtle)" />
              <Tooltip
                contentStyle={{ backgroundColor: 'var(--bg-secondary)', borderColor: 'var(--border-subtle)', color: 'var(--text-primary)', borderRadius: 8 }}
              />
              <Area type="monotone" dataKey={yAxisKey} stroke="var(--accent-gpt)" fillOpacity={1} fill="url(#chartColor)" strokeWidth={2} />
            </AreaChart>
          </ResponsiveContainer>
        </div>
      )}

      {viewType === 'bar' && yAxisKey && xAxisKey && (
        <div style={{ width: '100%', height: 240 }}>
          <ResponsiveContainer width="99%" height="100%">
            <BarChart data={chartData} margin={{ top: 10, right: 10, left: -10, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="var(--border-subtle)" />
              <XAxis dataKey={xAxisKey} tick={{ fill: 'var(--text-secondary)', fontSize: 11 }} stroke="var(--border-subtle)" />
              <YAxis tick={{ fill: 'var(--text-secondary)', fontSize: 11 }} stroke="var(--border-subtle)" />
              <Tooltip
                contentStyle={{ backgroundColor: 'var(--bg-secondary)', borderColor: 'var(--border-subtle)', color: 'var(--text-primary)', borderRadius: 8 }}
              />
              <Bar dataKey={yAxisKey} fill="var(--accent-gpt)" radius={[4, 4, 0, 0]} maxBarSize={45} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      )}

      {viewType === 'table' && (
        <div className="data-table-container">
          <table className="data-table">
            <thead>
              <tr>
                {keys.map(key => (
                  <th key={key}>{key}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {results.slice(0, 10).map((row, idx) => (
                <tr key={`row-${idx}`}>
                  {keys.map(key => (
                    <td key={key}>{String(row[key])}</td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
          {results.length > 10 && (
            <div style={{ padding: '6px 12px', fontSize: '11px', textAlign: 'center', backgroundColor: 'var(--bg-sidebar)', color: 'var(--text-muted)' }}>
              Showing first 10 of {results.length} rows
            </div>
          )}
        </div>
      )}
    </div>
  )
}

// =====================================================================
// PARSER FOR USER-READY TEXT (CLEANS MARKDOWN CHARACTERS)
// =====================================================================
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
          <span className="bullet-dot">•</span>
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

// =====================================================================
// MAIN CHATGPT LIGHT APP COMPONENT
// =====================================================================
function App() {
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [sidebarOpen, setSidebarOpen] = useState(true)
  const [docModalOpen, setDocModalOpen] = useState(false)
  const [analyticsModalOpen, setAnalyticsModalOpen] = useState(false)

  const [sessionId, setSessionId] = useState<string>(() => {
    const sid = localStorage.getItem('ai_analyst_session_id')
    if (!sid || !/^[a-zA-Z0-9_-]+$/.test(sid)) {
      const newSid = generateSessionId()
      localStorage.setItem('ai_analyst_session_id', newSid)
      return newSid
    }
    return sid
  })
  const [sessions, setSessions] = useState<SessionInfo[]>([])
  const scrollerRef = useRef<HTMLDivElement>(null)

  const loadSessionMessages = async (sid: string) => {
    if (!sid || !/^[a-zA-Z0-9_-]+$/.test(sid)) {
      return
    }
    try {
      const response = await fetch(`${API_BASE_URL}/sessions/${encodeURIComponent(sid)}/messages`)
      if (response.ok) {
        const data = await response.json()
        const formattedMessages = data.messages.map((m: ApiMessage) => ({
          id: `msg-${m.id}`,
          sender: m.sender as 'user' | 'agent',
          text: m.text,
          intent: m.intent,
          sql_generated: m.sql_generated,
          sql_results: m.sql_results,
          sources: m.sources,
          latency_seconds: m.latency_seconds,
          cached: m.cached,
          status: m.status
        }))
        setMessages(formattedMessages)
      }
    } catch (err) {
      console.error("Failed to load session messages:", err)
    }
  }

  const loadSessions = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/sessions`)
      if (response.ok) {
        const data = await response.json()
        let fetchedItems: SessionInfo[] = []
        if (data.session_items && data.session_items.length > 0) {
          fetchedItems = data.session_items
        } else if (data.sessions) {
          fetchedItems = data.sessions.map((sid: string) => ({ id: sid, title: sid }))
        }

        // Cache initial backend titles if not already stored
        fetchedItems.forEach(item => {
          if (item.title && !item.title.startsWith('sess-')) {
            saveStoredTitle(item.id, item.title)
          }
        })

        setSessions(fetchedItems)
      }
    } catch (err) {
      console.error("Failed to load sessions list:", err)
    }
  }

  useEffect(() => {
    if (sessionId) {
      loadSessionMessages(sessionId)
      loadSessions()
    }
  }, [sessionId])

  useEffect(() => {
    if (scrollerRef.current) {
      scrollerRef.current.scrollTop = scrollerRef.current.scrollHeight
    }
  }, [messages, loading])

  const handleSubmitQuery = async (queryText: string) => {
    if (!queryText.trim() || loading) return

    const userMessageId = `msg-user-${Date.now()}`
    const agentMessageId = `msg-agent-${Date.now()}`

    const userMsg: Message = {
      id: userMessageId,
      sender: 'user',
      text: queryText
    }

    // Lock session title ONCE to the very first prompt sent in this session
    saveStoredTitle(sessionId, queryText)

    setSessions(prev => {
      const storedMap = getStoredTitles()
      const titleToUse = storedMap[sessionId] || queryText
      const existing = prev.find(s => s.id === sessionId)
      if (existing) {
        return prev.map(s => s.id === sessionId ? { ...s, title: titleToUse } : s)
      }
      return [{ id: sessionId, title: titleToUse }, ...prev]
    })

    setMessages(prev => [...prev, userMsg])
    setInput('')
    setLoading(true)

    try {
      const response = await fetch(`${API_BASE_URL}/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query: queryText, session_id: sessionId })
      })

      if (!response.ok) {
        throw new Error(`Server returned HTTP ${response.status}`)
      }

      const data = await response.json()

      const agentMsg: Message = {
        id: agentMessageId,
        sender: 'agent',
        text: data.final_response,
        intent: data.intent,
        sql_generated: data.sql_generated,
        sql_results: data.sql_results,
        sources: data.sources,
        latency_seconds: data.latency_seconds,
        cached: data.cached,
        status: data.status
      }

      setMessages(prev => [...prev, agentMsg])
      loadSessions()
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : String(err)
      const errorMsg: Message = {
        id: agentMessageId,
        sender: 'agent',
        text: `Error processing query: ${errorMessage}. Please verify backend server is active on port 8000.`
      }
      setMessages(prev => [...prev, errorMsg])
    } finally {
      setLoading(false)
    }
  }

  const handleSuggestionClick = (query: string) => {
    handleSubmitQuery(query)
  }

  const handleNewChat = () => {
    const sid = generateSessionId()
    localStorage.setItem('ai_analyst_session_id', sid)
    setSessionId(sid)
    setMessages([])
  }

  const handleSelectSession = (sid: string) => {
    if (!sid || !/^[a-zA-Z0-9_-]+$/.test(sid)) return
    localStorage.setItem('ai_analyst_session_id', sid)
    setSessionId(sid)
  }

  const handleDeleteSession = async (e: React.SyntheticEvent, sid: string) => {
    e.stopPropagation()
    if (!sid || !/^[a-zA-Z0-9_-]+$/.test(sid)) return

    if (!window.confirm("Are you sure you want to delete this chat session?")) {
      return
    }

    try {
      const response = await fetch(`${API_BASE_URL}/sessions/${encodeURIComponent(sid)}`, {
        method: 'DELETE'
      })

      if (response.ok) {
        removeStoredTitle(sid)
        await loadSessions()
        if (sid === sessionId) {
          handleNewChat()
        }
      }
    } catch (err) {
      console.error("Failed to delete session:", err)
    }
  }

  return (
    <div className="dashboard-layout">
      {/* 1. CHATGPT LIGHT SIDEBAR */}
      <aside className={`sidebar ${sidebarOpen ? '' : 'closed'}`}>
        <div className="sidebar-header">
          <div className="sidebar-logo-row">
            <div className="brand-icon-gpt">A</div>
            <span className="brand-title">AI Analyst</span>
          </div>
          <button
            className="sidebar-toggle-btn"
            onClick={() => setSidebarOpen(false)}
            title="Close Sidebar"
          >
            <PanelLeft size={18} />
          </button>
        </div>

        <div className="sidebar-content">
          {/* New Chat Button */}
          <button className="new-chat-btn" onClick={handleNewChat}>
            <Plus size={16} /> New chat
          </button>

          {/* Feature Navigation Links */}
          <div className="sidebar-section">
            <button className="sidebar-nav-item" onClick={() => setDocModalOpen(true)}>
              <Database size={15} /> Document Library (RAG)
            </button>
            <button className="sidebar-nav-item" onClick={() => setAnalyticsModalOpen(true)}>
              <BarChart2 size={15} /> Business Analytics KPI
            </button>
          </div>

          {/* Session History List with Named Topics */}
          <div className="sidebar-section">
            <span className="sidebar-section-title">Recent Chats</span>
            {sessions.length > 0 ? (
              sessions.map(s => {
                const titleDisplay = formatSessionTitle(s.id, s.title)
                return (
                  <button
                    type="button"
                    key={s.id}
                    className={`session-item-row ${s.id === sessionId ? 'active' : ''}`}
                    onClick={() => handleSelectSession(s.id)}
                    title={titleDisplay}
                  >
                    <div className="session-item-left">
                      <MessageSquare size={14} style={{ flexShrink: 0, opacity: 0.7 }} />
                      <span className="session-item-text">
                        {titleDisplay}
                      </span>
                    </div>
                    <span
                      className="session-delete-btn"
                      onClick={(e) => handleDeleteSession(e, s.id)}
                      onKeyDown={(e) => {
                        if (e.key === 'Enter' || e.key === ' ') {
                          handleDeleteSession(e, s.id)
                        }
                      }}
                      title="Delete Chat"
                      role="button"
                      tabIndex={0}
                    >
                      <Trash2 size={13} />
                    </span>
                  </button>
                )
              })
            ) : (
              <div className="empty-sessions-hint">No recent chats</div>
            )}
          </div>
        </div>

        {/* User Footer */}
        <div className="sidebar-footer">
          <div className="user-profile-pill">
            <div className="user-avatar">SA</div>
            <div className="user-name-box">
              <span className="user-name">Sahil Negi</span>
              <span className="user-sub">Enterprise Plan</span>
            </div>
          </div>
        </div>
      </aside>

      {/* 2. MAIN CHAT AREA */}
      <main className="main-chat-area">
        {/* TOP NAVBAR (Stable Model Selector Button) */}
        <nav className="top-navbar">
          <div className="navbar-left">
            {!sidebarOpen && (
              <button className="sidebar-toggle-btn" onClick={() => setSidebarOpen(true)} title="Open Sidebar">
                <PanelLeft size={18} />
              </button>
            )}
            <button className="model-selector-btn" title="SQL & RAG Agent">
              <span>SQL & RAG Agent</span>
              <span className="model-version-tag">v1.0</span>
              <ChevronDown size={14} style={{ color: 'var(--text-muted)' }} />
            </button>
          </div>
        </nav>

        {/* CHAT MESSAGES CONTAINER */}
        <div className="chat-messages-scroller" ref={scrollerRef}>
          {messages.length === 0 ? (
            <div className="welcome-container">
              <div className="welcome-avatar-gpt">
                <Sparkles size={26} />
              </div>
              <h1 className="greeting-text">What would you like to analyze today?</h1>
              <p className="welcome-subtitle">
                Query relational SQL databases, summarize company SOP documents, or analyze revenue trends.
              </p>

              <div className="suggest-grid">
                <div className="suggest-card" onClick={() => handleSuggestionClick("Show top 5 products by revenue.")}>
                  <span className="suggest-card-title">Top Revenue Products</span>
                  <span className="suggest-card-desc">Calculate total product sales & rank top performers</span>
                </div>
                <div className="suggest-card" onClick={() => handleSuggestionClick("Why did sales decrease in March?")}>
                  <span className="suggest-card-title">Analyze March Dip</span>
                  <span className="suggest-card-desc">Correlate sales trends with logistical & warehouse SOP events</span>
                </div>
                <div className="suggest-card" onClick={() => handleSuggestionClick("What is the inventory turnover ratio?")}>
                  <span className="suggest-card-title">Inventory Turnover</span>
                  <span className="suggest-card-desc">Calculate COGS / Average Inventory from database records</span>
                </div>
                <div className="suggest-card" onClick={() => handleSuggestionClick("Summarize the inventory management SOP.")}>
                  <span className="suggest-card-title">Inventory SOP Summary</span>
                  <span className="suggest-card-desc">Search PDF vector store for cycle count & reorder guidelines</span>
                </div>
              </div>
            </div>
          ) : (
            <div className="messages-inner-container">
              {messages.map(msg => (
                <div key={msg.id} className={`chat-message-row ${msg.sender}`}>
                  {msg.sender === 'agent' && (
                    <div className="message-avatar agent">
                      <Sparkles size={16} />
                    </div>
                  )}

                  <div className="message-content">
                    {msg.sender === 'user' ? (
                      <div className="message-bubble-user">
                        {msg.text}
                      </div>
                    ) : (
                      <div className="message-bubble-agent">
                        {/* Render Markdown formatted text */}
                        <div className="formatted-text">{renderFormattedText(msg.text)}</div>

                        {/* SQL Visualized Chart or Table Widget */}
                        {msg.sql_results && (
                          <SqlResultsWidget results={msg.sql_results} />
                        )}

                        {/* RAG Context Attribution Cards */}
                        {msg.sources && msg.sources.length > 0 && (
                          <div className="retrieved-context-container">
                            <div className="context-header">
                              <span className="context-title">Retrieved SOP Context</span>
                              <span className="context-count-badge">{msg.sources.length} sources</span>
                            </div>

                            <div className="context-cards-list">
                              {msg.sources.map((src, idx) => (
                                <div key={`src-${src.filename}-${idx}`} className="retrieved-card">
                                  <div className="card-top-row">
                                    <span className="card-section-title">
                                      ≡ {src.title || src.filename}
                                    </span>
                                    <span className="card-char-count">
                                      Match: {Math.round(src.confidence * 100)}%
                                    </span>
                                  </div>
                                  <p className="card-body-snippet">{src.content_snippet}</p>
                                </div>
                              ))}
                            </div>
                          </div>
                        )}

                        {/* Metadata Bar */}
                        <div className="message-meta-bar">
                          {msg.intent && <span className="meta-pill">Intent: {msg.intent}</span>}
                          {msg.latency_seconds !== undefined && (
                            <span className="meta-pill">Latency: {msg.latency_seconds.toFixed(2)}s</span>
                          )}
                          {msg.cached !== undefined && (
                            <span className="meta-pill" style={{ color: msg.cached ? '#10a37f' : 'var(--text-muted)' }}>
                              {msg.cached ? 'Cache: Hit' : 'Cache: Miss'}
                            </span>
                          )}
                        </div>
                      </div>
                    )}
                  </div>

                  {msg.sender === 'user' && (
                    <div className="message-avatar user">
                      SA
                    </div>
                  )}
                </div>
              ))}

              {/* Typing Animation when waiting for agent */}
              {loading && (
                <div className="chat-message-row agent">
                  <div className="message-avatar agent">
                    <Sparkles size={16} />
                  </div>
                  <div className="message-content">
                    <div className="typing-indicator">
                      <span className="typing-dot" />
                      <span className="typing-dot" />
                      <span className="typing-dot" />
                    </div>
                  </div>
                </div>
              )}
            </div>
          )}
        </div>

        {/* 3. GROUNDED FLOATING INPUT BAR */}
        <div className="input-area-wrapper">
          <form
            onSubmit={(e) => {
              e.preventDefault()
              handleSubmitQuery(input)
            }}
            className="input-container"
          >
            <button
              type="button"
              className="attach-btn"
              onClick={() => setDocModalOpen(true)}
              title="Upload PDF Document into RAG Knowledge Base"
            >
              <Paperclip size={18} />
            </button>
            <input
              type="text"
              className="input-field"
              placeholder="Ask a question about sales, inventory, or company SOPs..."
              value={input}
              onChange={(e) => setInput(e.target.value)}
              disabled={loading}
            />
            <button type="submit" className="send-btn" disabled={loading || !input.trim()} title="Send query">
              <ArrowUp size={18} />
            </button>
          </form>
          <div className="input-disclaimer">
            AI Analyst can execute SQL queries and search document RAG memory.
          </div>
        </div>
      </main>

      {/* RAG DOCUMENT MANAGEMENT MODAL */}
      <DocumentModal
        isOpen={docModalOpen}
        onClose={() => setDocModalOpen(false)}
        apiBaseUrl={API_BASE_URL}
      />

      {/* BUSINESS ANALYTICS REPORT MODAL */}
      <AnalyticsModal
        isOpen={analyticsModalOpen}
        onClose={() => setAnalyticsModalOpen(false)}
        apiBaseUrl={API_BASE_URL}
      />
    </div>
  )
}

export default App
