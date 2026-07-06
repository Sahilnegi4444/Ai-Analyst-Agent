import React, { useState, useEffect, useRef } from 'react'
import {
  Send,
  Database,
  BookOpen,
  BarChart3,
  AlertTriangle,
  Menu,
  X,
  Table2,
  Layers,
  ChevronDown,
  ChevronRight,
  Sparkles,
  FileText,
  Clock,
  Zap,
  Info
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

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

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

// =====================================================================
// DATABASE SCHEMA METADATA DEFINITION
// =====================================================================
const DB_SCHEMA_METADATA = [
  {
    name: 'sales',
    description: 'Contains customer purchase logs, totals, and timestamps.',
    columns: [
      { name: 'transaction_id', type: 'VARCHAR(50) [PK]' },
      { name: 'customer_id', type: 'VARCHAR(50) [FK]' },
      { name: 'product_id', type: 'VARCHAR(50) [FK]' },
      { name: 'quantity', type: 'INTEGER' },
      { name: 'total_amount', type: 'NUMERIC(10,2)' },
      { name: 'transaction_date', type: 'TIMESTAMP' },
      { name: 'store_location', type: 'VARCHAR(100)' }
    ]
  },
  {
    name: 'inventory',
    description: 'Active warehouse stock quantities and reorder thresholds.',
    columns: [
      { name: 'product_id', type: 'VARCHAR(50) [PK]' },
      { name: 'current_stock', type: 'INTEGER' },
      { name: 'reorder_level', type: 'INTEGER' },
      { name: 'reorder_quantity', type: 'INTEGER' },
      { name: 'last_restock_date', type: 'TIMESTAMP' }
    ]
  },
  {
    name: 'products',
    description: 'Detailed specifications and pricing for the product catalog.',
    columns: [
      { name: 'product_id', type: 'VARCHAR(50) [PK]' },
      { name: 'product_name', type: 'VARCHAR(150)' },
      { name: 'category', type: 'VARCHAR(100)' },
      { name: 'price', type: 'NUMERIC(10,2)' },
      { name: 'supplier_id', type: 'VARCHAR(50) [FK]' }
    ]
  },
  {
    name: 'returns',
    description: 'Log of product returns, dates, and refunded amounts.',
    columns: [
      { name: 'return_id', type: 'VARCHAR(50) [PK]' },
      { name: 'transaction_id', type: 'VARCHAR(50) [FK]' },
      { name: 'return_date', type: 'TIMESTAMP' },
      { name: 'reason', type: 'TEXT' },
      { name: 'refund_amount', type: 'NUMERIC(10,2)' }
    ]
  },
  {
    name: 'reviews',
    description: 'Customer ratings and text feedback reviews per product.',
    columns: [
      { name: 'review_id', type: 'VARCHAR(50) [PK]' },
      { name: 'product_id', type: 'VARCHAR(50) [FK]' },
      { name: 'customer_id', type: 'VARCHAR(50) [FK]' },
      { name: 'rating', type: 'INTEGER' },
      { name: 'review_text', type: 'TEXT' },
      { name: 'review_date', type: 'TIMESTAMP' }
    ]
  },
  {
    name: 'suppliers',
    description: 'External fulfillment vendors and standard lead times.',
    columns: [
      { name: 'supplier_id', type: 'VARCHAR(50) [PK]' },
      { name: 'supplier_name', type: 'VARCHAR(150)' },
      { name: 'contact_name', type: 'VARCHAR(100)' },
      { name: 'email', type: 'VARCHAR(150)' },
      { name: 'lead_time_days', type: 'INTEGER' }
    ]
  }
];

// =====================================================================
// SQL RESULTS WIDGET COMPONENT
// =====================================================================
const SqlResultsWidget: React.FC<{ results: Record<string, unknown>[] }> = ({ results }) => {
  const firstRow = results && results.length > 0 ? results[0] : null
  const keys = firstRow ? Object.keys(firstRow) : []

  // Identify label keys (X-axis)
  const dateKeys = keys.filter(key => {
    const name = key.toLowerCase()
    return name.includes('month') || name.includes('date') || name.includes('week') || name.includes('year')
  })

  // Identify numeric keys (excluding IDs and dates)
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
              <BarChart3 size={15} className="widget-title-icon" />
              Visualized Trend Line
            </>
          )}
          {viewType === 'bar' && (
            <>
              <BarChart3 size={15} className="widget-title-icon" />
              Relevance Bar Comparison (Top 5)
            </>
          )}
          {viewType === 'table' && (
            <>
              <Table2 size={15} className="widget-title-icon" />
              Database Records ({results.length} rows)
            </>
          )}
        </span>
        <div className="widget-controls">
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

      <div className="widget-display-area">
        {viewType === 'area' && yAxisKey && xAxisKey && (
          <div style={{ width: '100%', height: 260 }}>
            <ResponsiveContainer width="99%" height="100%">
              <AreaChart data={chartData} margin={{ top: 10, right: 10, left: -10, bottom: 0 }}>
                <defs>
                  <linearGradient id="chartColor" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="var(--accent-brand)" stopOpacity={0.3} />
                    <stop offset="95%" stopColor="var(--accent-brand)" stopOpacity={0.0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
                <XAxis dataKey={xAxisKey} tick={{ fill: 'var(--text)', fontSize: 10 }} stroke="var(--border)" />
                <YAxis tick={{ fill: 'var(--text)', fontSize: 10 }} stroke="var(--border)" />
                <Tooltip
                  contentStyle={{ backgroundColor: 'var(--bg-panel)', borderColor: 'var(--border)', color: 'var(--text-h)', borderRadius: 8, fontSize: 12 }}
                />
                <Area type="monotone" dataKey={yAxisKey} stroke="var(--accent-brand)" fillOpacity={1} fill="url(#chartColor)" strokeWidth={2.5} />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        )}

        {viewType === 'bar' && yAxisKey && xAxisKey && (
          <div style={{ width: '100%', height: 260 }}>
            <ResponsiveContainer width="99%" height="100%">
              <BarChart data={chartData} margin={{ top: 10, right: 10, left: -10, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
                <XAxis dataKey={xAxisKey} tick={{ fill: 'var(--text)', fontSize: 10 }} stroke="var(--border)" />
                <YAxis tick={{ fill: 'var(--text)', fontSize: 10 }} stroke="var(--border)" />
                <Tooltip
                  contentStyle={{ backgroundColor: 'var(--bg-panel)', borderColor: 'var(--border)', color: 'var(--text-h)', borderRadius: 8, fontSize: 12 }}
                />
                <Bar dataKey={yAxisKey} fill="var(--accent-brand)" radius={[4, 4, 0, 0]} maxBarSize={45} />
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
                  <tr key={idx}>
                    {keys.map(key => (
                      <td key={key}>{String(row[key])}</td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
            {results.length > 10 && (
              <div className="table-truncation-banner">
                Showing first 10 of {results.length} rows
              </div>
            )}
          </div>
        )}
      </div>
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
  const [expandedTable, setExpandedTable] = useState<string | null>(null)
  const [activeCitation, setActiveCitation] = useState<string | null>(null)
  const scrollerRef = useRef<HTMLDivElement>(null)

  // Verify Backend Connectivity on Startup
  useEffect(() => {
    fetch(`${API_BASE_URL}/health`)
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
      const response = await fetch(`${API_BASE_URL}/chat`, {
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
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : String(err)
      const errorMsg: Message = {
        id: agentMessageId,
        sender: 'agent',
        text: `Error processing query: ${errorMessage}. Make sure the backend service is running and correctly deployed.`
      }
      setMessages(prev => [...prev, errorMsg])
    } finally {
      setLoading(false)
    }
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
            <Layers size={20} className="sidebar-logo-icon" />
            <span>AI Analyst</span>
            <span className="version-pill">v2.1</span>
          </div>
          <button className="menu-toggle" onClick={() => setSidebarOpen(false)}>
            <X size={16} />
          </button>
        </div>

        <div className="sidebar-content">
          {/* Section 1: Suggested Prompts */}
          <div className="sidebar-section">
            <span className="sidebar-title">Suggested Inquiries</span>
            <div className="sidebar-button-group">
              <button className="sidebar-btn" onClick={() => handleSuggestionClick("Show top 5 products by revenue.")}>
                <BarChart3 size={14} className="icon-indigo" />
                <span>Top 5 Revenue Products</span>
              </button>
              <button className="sidebar-btn" onClick={() => handleSuggestionClick("Why did sales decrease in March?")}>
                <AlertTriangle size={14} className="icon-warn" />
                <span>Explain March Sales Dip</span>
              </button>
              <button className="sidebar-btn" onClick={() => handleSuggestionClick("What is the inventory turnover ratio?")}>
                <Database size={14} className="icon-success" />
                <span>Inventory Turnover Ratio</span>
              </button>
              <button className="sidebar-btn" onClick={() => handleSuggestionClick("Summarize the inventory management SOP.")}>
                <BookOpen size={14} className="icon-info" />
                <span>Summarize Inventory SOP</span>
              </button>
            </div>
          </div>

          {/* Section 2: Interactive Database Schema Explorer */}
          <div className="sidebar-section">
            <span className="sidebar-title">Schema Explorer</span>
            <div className="schema-explorer">
              {DB_SCHEMA_METADATA.map(table => (
                <div key={table.name} className="schema-table-card">
                  <button 
                    className={`schema-table-trigger ${expandedTable === table.name ? 'active' : ''}`}
                    onClick={() => setExpandedTable(expandedTable === table.name ? null : table.name)}
                  >
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px', overflow: 'hidden' }}>
                      <Table2 size={13} className="table-card-icon" />
                      <span className="table-name-text">{table.name}</span>
                    </div>
                    {expandedTable === table.name ? <ChevronDown size={12} /> : <ChevronRight size={12} />}
                  </button>
                  {expandedTable === table.name && (
                    <div className="schema-table-details">
                      <p className="schema-table-desc">{table.description}</p>
                      <div className="schema-column-list">
                        {table.columns.map(col => (
                          <div key={col.name} className="schema-column-item">
                            <span className="column-name">{col.name}</span>
                            <span className="column-type">{col.type}</span>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>
        </div>

        <div className="sidebar-footer">
          <div className={`status-badge ${apiOnline === 'online' ? 'online' : 'offline'}`}>
            <span className="indicator" />
            <span>Backend: {apiOnline === 'online' ? 'Online' : 'Offline'}</span>
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
                <Menu size={18} />
              </button>
            )}
            <div>
              <h2 className="navbar-heading">Data Analyst Portal</h2>
              <span className="navbar-subheading">Enterprise SQL & RAG Agent</span>
            </div>
          </div>
          <div className="navbar-right">
            <div className="workspace-tag">
              <span className="workspace-dot" />
              <span>Workspace: Retail_Sales_2025</span>
            </div>
          </div>
        </nav>

        {/* MESSAGES WORKSPACE */}
        <div className="chat-messages-scroller" ref={scrollerRef}>
          {messages.length === 0 ? (
            <div className="welcome-container">
              <div className="welcome-icon-wrapper">
                <Sparkles className="sparkles-hero-icon" size={32} />
              </div>
              <h1 className="greeting-text">Welcome, Analyst</h1>
              <p className="welcome-subtitle">
                Query relational metrics, read logistics manuals, calculate MoM sales, or audit vendor agreements.
              </p>

              <div className="suggest-grid">
                <div className="suggest-card" onClick={() => handleSuggestionClick("Show top 5 products by revenue.")}>
                  <div className="suggest-card-header">
                    <BarChart3 size={16} className="icon-indigo" />
                    <span className="suggest-card-title">Top 5 Products</span>
                  </div>
                  <p className="suggest-card-desc">Execute an SQL query to analyze catalog revenues and performance.</p>
                </div>
                
                <div className="suggest-card" onClick={() => handleSuggestionClick("Why did sales decrease in March?")}>
                  <div className="suggest-card-header">
                    <AlertTriangle size={16} className="icon-warn" />
                    <span className="suggest-card-title">Explain March Drop</span>
                  </div>
                  <p className="suggest-card-desc">Conduct a hybrid analysis linking database figures with SOP events.</p>
                </div>
                
                <div className="suggest-card" onClick={() => handleSuggestionClick("What is the inventory turnover ratio?")}>
                  <div className="suggest-card-header">
                    <Database size={16} className="icon-success" />
                    <span className="suggest-card-title">Inventory Turnover</span>
                  </div>
                  <p className="suggest-card-desc">Perform mathematical KPI formulas across inventory stocks.</p>
                </div>
                
                <div className="suggest-card" onClick={() => handleSuggestionClick("Summarize the inventory management SOP.")}>
                  <div className="suggest-card-header">
                    <BookOpen size={16} className="icon-info" />
                    <span className="suggest-card-title">Summarize SOP</span>
                  </div>
                  <p className="suggest-card-desc">Search PDF documentation for cycle count policies and rules.</p>
                </div>
              </div>
            </div>
          ) : (
            <div className="messages-feed-wrapper">
              {messages.map(msg => (
                <div key={msg.id} className={`chat-message-wrapper ${msg.sender}`}>
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
                                <Database size={12} />
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
                        <div className="citations-panel">
                          <span className="citations-panel-heading">
                            <BookOpen size={12} />
                            <span>Retrieved Document Sources</span>
                          </span>
                          <div className="citations-list">
                            {msg.sources.map((src, idx) => {
                              const cardId = `${msg.id}-src-${idx}`
                              const isCollapsed = activeCitation !== cardId
                              return (
                                <div key={idx} className="citation-card">
                                  <button 
                                    className="citation-card-header"
                                    onClick={() => setActiveCitation(isCollapsed ? cardId : null)}
                                  >
                                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                                      <FileText size={13} style={{ color: 'var(--accent-brand)' }} />
                                      <span className="citation-filename">{src.filename}</span>
                                    </div>
                                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                                      <span className="citation-match-badge">
                                        Match: {Math.round(src.confidence * 100)}%
                                      </span>
                                      {isCollapsed ? <ChevronRight size={13} /> : <ChevronDown size={13} />}
                                    </div>
                                  </button>
                                  {!isCollapsed && (
                                    <div className="citation-card-body">
                                      <p className="citation-snippet-text">{src.content_snippet}</p>
                                    </div>
                                  )}
                                </div>
                              )
                            })}
                          </div>
                        </div>
                      )}
                    </div>

                    {/* METRICS & RUNTIME STATS */}
                    {msg.sender === 'agent' && (msg.latency_seconds !== undefined || msg.cached !== undefined) && (
                      <div className="message-metrics-bar">
                        {msg.intent && (
                          <span className="metrics-pill text-indigo">
                            <Sparkles size={10} style={{ marginRight: '4px' }} />
                            Intent: {msg.intent}
                          </span>
                        )}
                        {msg.latency_seconds !== undefined && (
                          <span className="metrics-pill">
                            <Clock size={10} style={{ marginRight: '4px' }} />
                            Latency: {msg.latency_seconds.toFixed(2)}s
                          </span>
                        )}
                        {msg.cached !== undefined && (
                          <span className={`metrics-pill ${msg.cached ? 'cached-hit' : 'cached-miss'}`}>
                            <Zap size={10} style={{ marginRight: '4px' }} />
                            {msg.cached ? 'Cache Hit' : 'Cache Miss'}
                          </span>
                        )}
                      </div>
                    )}
                  </div>
                </div>
              ))}

              {/* Bouncing Dots Loading Animation */}
              {loading && (
                <div className="chat-message-wrapper agent" style={{ marginBottom: '16px' }}>
                  <div className="message-bubble-container agent">
                    <div className="message-sender-identity">AI Agent</div>
                    <div className="message-bubble agent">
                      <div className="typing-indicator">
                        <span className="typing-dot" />
                        <span className="typing-dot" />
                        <span className="typing-dot" />
                      </div>
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
              placeholder="Query sales databases or fetch policies..."
              value={input}
              onChange={(e) => setInput(e.target.value)}
              disabled={loading}
            />
            <button type="submit" className="send-btn" disabled={loading || !input.trim()}>
              <Send size={16} />
            </button>
          </form>
          <div className="disclaimer-text">
            <Info size={11} style={{ verticalAlign: 'middle', marginRight: '4px', display: 'inline-block' }} />
            Antigravity SQL Sandbox environment compiles safe read-only queries with caching enabled.
          </div>
        </div>
      </main>
    </div>
  )
}

export default App
