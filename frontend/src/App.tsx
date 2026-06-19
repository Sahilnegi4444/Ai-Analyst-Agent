import React, { useState, useEffect, useRef } from 'react'
import {
  Send,
  Database,
  BookOpen,
  BarChart3,
  AlertTriangle,
  ChevronDown,
  ChevronUp,
  Menu,
  X,
  Terminal,
  Table2,
  Layers
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
import './App.css'

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
  sql_results?: any[] | null
  sources?: Source[] | null
  latency_seconds?: number
  cached?: boolean
  status?: string
}

// =====================================================================
// SQL RESULTS WIDGET COMPONENT
// =====================================================================
const SqlResultsWidget: React.FC<{ results: any[] }> = ({ results }) => {
  // Analyze the data structure
  const firstRow = results && results.length > 0 ? results[0] : null
  const keys = firstRow ? Object.keys(firstRow) : []

  // Identify label keys (X-axis)
  const dateKeys = keys.filter(key => {
    const name = key.toLowerCase()
    return name.includes('month') || name.includes('date') || name.includes('week') || name.includes('year')
  })

  // Identify numeric keys (excluding potential primary/foreign IDs and date-related fields)
  const numericKeys = keys.filter(key => {
    const val = firstRow[key]
    const isId = key.toLowerCase().includes('id')
    const isDate = dateKeys.includes(key)
    return typeof val === 'number' && !isId && !isDate
  })

  const labelKeys = keys.filter(key => {
    const isNum = numericKeys.includes(key)
    return !isNum
  })

  // Determine standard configurations
  const yAxisKey = numericKeys[0] || null

  // Prioritize date, then week, then month, then year for X-axis key to prevent year-only labeling
  const prioritizedDateKeys = [...dateKeys].sort((a, b) => {
    const order = ['date', 'week', 'month', 'year']
    const idxA = order.findIndex(term => a.toLowerCase().includes(term))
    const idxB = order.findIndex(term => b.toLowerCase().includes(term))
    return idxA - idxB
  })
  const xAxisKey = prioritizedDateKeys[0] || labelKeys[0] || null

  // If no columns are suitable for plotting, default to table view
  const canPlot = !!(yAxisKey && xAxisKey)
  const isChronological = dateKeys.length > 0

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
              <BarChart3 size={16} style={{ verticalAlign: 'middle', marginRight: '6px' }} />
              Visualized Results (Line Trend)
            </>
          )}
          {viewType === 'bar' && (
            <>
              <BarChart3 size={16} style={{ verticalAlign: 'middle', marginRight: '6px' }} />
              Visualized Results (Bar Comparison)
            </>
          )}
          {viewType === 'table' && (
            <>
              <Table2 size={16} style={{ verticalAlign: 'middle', marginRight: '6px' }} />
              Raw Database Records ({results.length} rows)
            </>
          )}
        </span>
        <div className="widget-controls" style={{ display: 'flex', gap: '6px' }}>
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
        <div style={{ width: '100%', height: 260 }}>
          <ResponsiveContainer width="99%" height="100%">
            <AreaChart data={results} margin={{ top: 10, right: 10, left: -10, bottom: 0 }}>
              <defs>
                <linearGradient id="chartColor" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="var(--accent)" stopOpacity={0.4} />
                  <stop offset="95%" stopColor="var(--accent)" stopOpacity={0.0} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
              <XAxis dataKey={xAxisKey} tick={{ fill: 'var(--text)', fontSize: 11 }} stroke="var(--border)" />
              <YAxis tick={{ fill: 'var(--text)', fontSize: 11 }} stroke="var(--border)" />
              <Tooltip
                contentStyle={{ backgroundColor: 'var(--panel-bg)', borderColor: 'var(--border)', color: 'var(--text-h)', borderRadius: 8 }}
              />
              <Area type="monotone" dataKey={yAxisKey} stroke="var(--accent)" fillOpacity={1} fill="url(#chartColor)" strokeWidth={2} />
            </AreaChart>
          </ResponsiveContainer>
        </div>
      )}

      {viewType === 'bar' && yAxisKey && xAxisKey && (
        <div style={{ width: '100%', height: 260 }}>
          <ResponsiveContainer width="99%" height="100%">
            <BarChart data={results} margin={{ top: 10, right: 10, left: -10, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
              <XAxis dataKey={xAxisKey} tick={{ fill: 'var(--text)', fontSize: 11 }} stroke="var(--border)" />
              <YAxis tick={{ fill: 'var(--text)', fontSize: 11 }} stroke="var(--border)" />
              <Tooltip
                contentStyle={{ backgroundColor: 'var(--panel-bg)', borderColor: 'var(--border)', color: 'var(--text-h)', borderRadius: 8 }}
              />
              <Bar dataKey={yAxisKey} fill="var(--accent)" radius={[4, 4, 0, 0]} maxBarSize={45} />
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
              {results.slice(0, 30).map((row, idx) => (
                <tr key={idx}>
                  {keys.map(key => (
                    <td key={key}>{String(row[key])}</td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
          {results.length > 30 && (
            <div style={{ padding: '8px 12px', fontSize: '11px', textAlign: 'center', backgroundColor: 'var(--code-bg)', borderTop: '1px solid var(--border)' }}>
              Showing first 30 of {results.length} rows
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
// MAIN APP COMPONENT
// =====================================================================
function App() {
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [sidebarOpen, setSidebarOpen] = useState(true)
  const [apiOnline, setApiOnline] = useState<'checking' | 'online' | 'offline'>('checking')
  const [expandedSql, setExpandedSql] = useState<{ [key: string]: boolean }>({})
  const scrollerRef = useRef<HTMLDivElement>(null)

  // Verify Backend Connectivity on Startup
  useEffect(() => {
    fetch('http://localhost:8000/')
      .then(res => {
        if (res.ok) setApiOnline('online')
        else setApiOnline('offline')
      })
      .catch(() => setApiOnline('offline'))
  }, [])

  // Auto Scroll to Bottom on Messages Update
  useEffect(() => {
    if (scrollerRef.current) {
      scrollerRef.current.scrollTop = scrollerRef.current.scrollHeight
    }
  }, [messages, loading])

  // Submit Query to Agent Endpoint
  const handleSubmitQuery = async (queryText: string) => {
    if (!queryText.trim() || loading) return

    const userMessageId = `msg-user-${Date.now()}`
    const agentMessageId = `msg-agent-${Date.now()}`

    // Append User message
    const userMsg: Message = {
      id: userMessageId,
      sender: 'user',
      text: queryText
    }
    setMessages(prev => [...prev, userMsg])
    setInput('')
    setLoading(true)

    try {
      const response = await fetch('http://localhost:8000/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query: queryText })
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
    } catch (err: any) {
      const errorMsg: Message = {
        id: agentMessageId,
        sender: 'agent',
        text: `Error processing query: ${err.message || err}. Make sure the FastAPI backend is running on port 8000.`
      }
      setMessages(prev => [...prev, errorMsg])
    } finally {
      setLoading(false)
    }
  }

  // Toggle Accordion Drawer for SQL query
  const toggleSql = (msgId: string) => {
    setExpandedSql(prev => ({
      ...prev,
      [msgId]: !prev[msgId]
    }))
  }

  // Quick template trigger
  const handleSuggestionClick = (query: string) => {
    handleSubmitQuery(query)
  }

  return (
    <div className="dashboard-layout">
      {/* 1. LEFT SIDEBAR PANEL */}
      <aside className={`sidebar ${sidebarOpen ? '' : 'closed'}`}>
        <div className="sidebar-header">
          <div className="sidebar-logo">
            <Layers size={22} style={{ color: 'var(--accent)' }} />
            <span>AI Analyst</span>
          </div>
          <button className="menu-toggle" onClick={() => setSidebarOpen(false)} style={{ color: '#fff' }}>
            <X size={18} />
          </button>
        </div>

        <div className="sidebar-content">
          <div className="sidebar-section">
            <span className="sidebar-title">Suggested Prompts</span>
            <button className="sidebar-btn" onClick={() => handleSuggestionClick("Show top 5 products by revenue.")}>
              <BarChart3 size={14} /> Top 5 Revenue Products
            </button>
            <button className="sidebar-btn" onClick={() => handleSuggestionClick("Why did sales decrease in March?")}>
              <AlertTriangle size={14} /> Explain March Dip
            </button>
            <button className="sidebar-btn" onClick={() => handleSuggestionClick("What is the inventory turnover ratio?")}>
              <Database size={14} /> Inventory Turnover
            </button>
            <button className="sidebar-btn" onClick={() => handleSuggestionClick("Summarize the inventory management SOP.")}>
              <BookOpen size={14} /> Inventory SOP
            </button>
          </div>
        </div>

        <div className="sidebar-footer">
          <div className={`status-badge ${apiOnline === 'online' ? 'online' : 'offline'}`}>
            <span className="indicator" />
            <span>Backend: {apiOnline === 'online' ? 'Online (8000)' : 'Offline'}</span>
          </div>
        </div>
      </aside>

      {/* 2. MAIN CHAT AREA */}
      <main className="main-chat-area">
        {/* TOP MENU NAVBAR */}
        <nav className="top-navbar">
          <div className="navbar-left">
            {!sidebarOpen && (
              <button className="menu-toggle" onClick={() => setSidebarOpen(true)}>
                <Menu size={20} />
              </button>
            )}
            <h2 style={{ fontSize: '18px', margin: 0, fontWeight: 600, color: 'var(--text-h)' }}>
              Data Analyst Agent
            </h2>
          </div>
          <span style={{ fontSize: '11px', color: 'var(--text)' }}>
            Enterprise Workspace
          </span>
        </nav>

        {/* MESSAGES WORKSPACE */}
        <div className="chat-messages-scroller" ref={scrollerRef}>
          {messages.length === 0 ? (
            <div className="welcome-container">
              <h1 className="greeting-text">Hello, Data Analyst</h1>
              <p className="welcome-subtitle">
                Ask me to run queries, fetch SOP documentation, calculate turnover, or analyze business trends.
              </p>

              <div className="suggest-grid">
                <div className="suggest-card" onClick={() => handleSuggestionClick("Show top 5 products by revenue.")}>
                  <div className="suggest-card-title">Top 5 Products</div>
                  <div className="suggest-card-desc">Calculates product revenues and lists top performers.</div>
                </div>
                <div className="suggest-card" onClick={() => handleSuggestionClick("Why did sales decrease in March?")}>
                  <div className="suggest-card-title">Analyze Sales Drop</div>
                  <div className="suggest-card-desc">Correlates database trends with March logistical events.</div>
                </div>
                <div className="suggest-card" onClick={() => handleSuggestionClick("What is the inventory turnover ratio?")}>
                  <div className="suggest-card-title">Inventory Turnover</div>
                  <div className="suggest-card-desc">Calculates COGS / Average Inventory from historical records.</div>
                </div>
                <div className="suggest-card" onClick={() => handleSuggestionClick("Summarize the inventory management SOP.")}>
                  <div className="suggest-card-title">Summarize SOP</div>
                  <div className="suggest-card-desc">Retrieves and lists cycle counts and reorder guidelines.</div>
                </div>
              </div>
            </div>
          ) : (
            <div style={{ maxWidth: '880px', margin: '0 auto' }}>
              {messages.map(msg => (
                <div key={msg.id} className="chat-message-wrapper">
                  <div className={`message-bubble ${msg.sender}`}>
                    {/* Render cleaned and formatted text body */}
                    <div className="formatted-text">{renderFormattedText(msg.text)}</div>

                    {/* DYNAMIC CHARTING & TABLE WIDGET (SQL RESULTS) */}
                    {msg.sender === 'agent' && msg.sql_results && (
                      <SqlResultsWidget results={msg.sql_results} />
                    )}

                    {/* RAG CITATIONS WIDGET */}
                    {msg.sender === 'agent' && msg.sources && msg.sources.length > 0 && (
                      <div className="citations-panel">
                        <span style={{ fontSize: '12px', fontWeight: 600, color: 'var(--text-h)', display: 'flex', alignItems: 'center', gap: '6px', marginBottom: '8px' }}>
                          <BookOpen size={14} /> References
                        </span>
                        {msg.sources.map((src, idx) => (
                          <div key={idx} className="citation-card" style={{ padding: '10px 14px' }}>
                            <div className="citation-meta" style={{ margin: 0 }}>
                              <span>Source: {src.filename}</span>
                              <span style={{ color: 'var(--accent)' }}>Match: {Math.round(src.confidence * 100)}%</span>
                            </div>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>

                  {/* LOGS METRICS AND CACHE BADGES */}
                  {msg.sender === 'agent' && (msg.latency_seconds !== undefined || msg.cached !== undefined) && (
                    <div className="message-meta">
                      {msg.intent && <span className="meta-pill">Intent: {msg.intent}</span>}
                      {msg.latency_seconds !== undefined && (
                        <span className="meta-pill">Latency: {msg.latency_seconds.toFixed(2)}s</span>
                      )}
                      {msg.cached !== undefined && (
                        <span className="meta-pill" style={{ color: msg.cached ? '#10b981' : '#f59e0b', fontWeight: 600 }}>
                          {msg.cached ? 'Cache: Hit' : 'Cache: Miss'}
                        </span>
                      )}
                    </div>
                  )}
                </div>
              ))}

              {/* Bouncing Dots Loading Animation */}
              {loading && (
                <div className="chat-message-wrapper" style={{ alignItems: 'flex-start' }}>
                  <div className="message-bubble agent">
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

        {/* BOTTOM INPUT PILLED FORM */}
        <div className="input-area-wrapper">
          <form
            onSubmit={(e) => {
              e.preventDefault()
              handleSubmitQuery(input)
            }}
            className="input-container"
          >
            <input
              type="text"
              className="input-field"
              placeholder="Ask the BI Analyst..."
              value={input}
              onChange={(e) => setInput(e.target.value)}
              disabled={loading}
            />
            <button type="submit" className="send-btn" disabled={loading || !input.trim()}>
              <Send size={18} />
            </button>
          </form>
          <div className="disclaimer-text">
            Antigravity BI executes safe read-only queries. Calculations are pre-computed via Pandas.
          </div>
        </div>
      </main>
    </div>
  )
}

export default App
