import { useState, useEffect, useRef } from 'react'
import {
  Layers,
  BarChart3,
  AlertTriangle,
  Database,
  BookOpen,
  Sparkles,
  X,
  Menu
} from 'lucide-react'
import { SchemaExplorer } from './components/SchemaExplorer/SchemaExplorer'
import type { TableSchema } from './components/SchemaExplorer/SchemaExplorer'
import { ChatInput } from './components/ChatInput/ChatInput'
import { MessageFeed } from './components/MessageFeed/MessageFeed'
import type { Message } from './components/MessageFeed/MessageItem'
import './App.css'

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const DB_SCHEMA_METADATA: TableSchema[] = [
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

function App() {
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [sidebarOpen, setSidebarOpen] = useState(true)
  const [apiOnline, setApiOnline] = useState<'checking' | 'online' | 'offline'>('checking')
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
            <Layers size={20} className="sidebar-logo-icon" aria-hidden="true" />
            <span>AI Analyst</span>
            <span className="version-pill">v2.1</span>
          </div>
          <button className="menu-toggle" onClick={() => setSidebarOpen(false)} aria-label="Close sidebar">
            <X size={16} aria-hidden="true" />
          </button>
        </div>

        <div className="sidebar-content">
          {/* Section 1: Suggested Prompts */}
          <div className="sidebar-section">
            <span className="sidebar-title">Suggested Inquiries</span>
            <div className="sidebar-button-group">
              <button className="sidebar-btn" onClick={() => handleSuggestionClick("Show top 5 products by revenue.")} aria-label="Query top 5 products by revenue">
                <BarChart3 size={14} className="icon-teal" aria-hidden="true" />
                <span>Top 5 Revenue Products</span>
              </button>
              <button className="sidebar-btn" onClick={() => handleSuggestionClick("Why did sales decrease in March?")} aria-label="Query why sales decreased in March">
                <AlertTriangle size={14} className="icon-warn" aria-hidden="true" />
                <span>Explain March Sales Dip</span>
              </button>
              <button className="sidebar-btn" onClick={() => handleSuggestionClick("What is the inventory turnover ratio?")} aria-label="Query inventory turnover ratio">
                <Database size={14} className="icon-success" aria-hidden="true" />
                <span>Inventory Turnover Ratio</span>
              </button>
              <button className="sidebar-btn" onClick={() => handleSuggestionClick("Summarize the inventory management SOP.")} aria-label="Query summary of inventory management SOP">
                <BookOpen size={14} className="icon-info" aria-hidden="true" />
                <span>Summarize Inventory SOP</span>
              </button>
            </div>
          </div>

          {/* Section 2: Interactive Database Schema Explorer */}
          <div className="sidebar-section">
            <span className="sidebar-title">Schema Explorer</span>
            <SchemaExplorer schemaData={DB_SCHEMA_METADATA} />
          </div>
        </div>

        <div className="sidebar-footer">
          <div className={`status-badge ${apiOnline === 'online' ? 'online' : 'offline'}`} role="status">
            <span className="indicator" aria-hidden="true" />
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
              <button className="menu-toggle" onClick={() => setSidebarOpen(true)} aria-label="Open sidebar">
                <Menu size={18} aria-hidden="true" />
              </button>
            )}
            <div>
              <h2 className="navbar-heading">Data Analyst Portal</h2>
              <span className="navbar-subheading">Enterprise SQL & RAG Agent</span>
            </div>
          </div>
          <div className="navbar-right">
            <div className="workspace-tag">
              <span className="workspace-dot" aria-hidden="true" />
              <span>Workspace: Retail_Sales_2025</span>
            </div>
          </div>
        </nav>

        {/* MESSAGES WORKSPACE */}
        <div className="chat-messages-scroller" ref={scrollerRef}>
          {messages.length === 0 ? (
            <div className="welcome-container">
              <div className="welcome-icon-wrapper">
                <Sparkles className="sparkles-hero-icon" size={32} aria-hidden="true" />
              </div>
              <h1 className="greeting-text">Welcome, Analyst</h1>
              <p className="welcome-subtitle">
                Query relational metrics, read logistics manuals, calculate MoM sales, or audit vendor agreements.
              </p>

              <div className="suggest-grid">
                <button className="suggest-card" onClick={() => handleSuggestionClick("Show top 5 products by revenue.")} aria-label="Run top 5 products by revenue analysis">
                  <div className="suggest-card-header">
                    <BarChart3 size={16} className="icon-teal" aria-hidden="true" />
                    <span className="suggest-card-title">Top 5 Products</span>
                  </div>
                  <p className="suggest-card-desc">Execute an SQL query to analyze catalog revenues and performance.</p>
                </button>
                
                <button className="suggest-card" onClick={() => handleSuggestionClick("Why did sales decrease in March?")} aria-label="Run March sales drop explanation analysis">
                  <div className="suggest-card-header">
                    <AlertTriangle size={16} className="icon-warn" aria-hidden="true" />
                    <span className="suggest-card-title">Explain March Drop</span>
                  </div>
                  <p className="suggest-card-desc">Conduct a hybrid analysis linking database figures with SOP events.</p>
                </button>
                
                <button className="suggest-card" onClick={() => handleSuggestionClick("What is the inventory turnover ratio?")} aria-label="Calculate inventory turnover ratio">
                  <div className="suggest-card-header">
                    <Database size={16} className="icon-success" aria-hidden="true" />
                    <span className="suggest-card-title">Inventory Turnover</span>
                  </div>
                  <p className="suggest-card-desc">Perform mathematical KPI formulas across inventory stocks.</p>
                </button>
                
                <button className="suggest-card" onClick={() => handleSuggestionClick("Summarize the inventory management SOP.")} aria-label="Summarize inventory management SOP doc">
                  <div className="suggest-card-header">
                    <BookOpen size={16} className="icon-info" aria-hidden="true" />
                    <span className="suggest-card-title">Summarize SOP</span>
                  </div>
                  <p className="suggest-card-desc">Search PDF documentation for cycle count policies and rules.</p>
                </button>
              </div>
            </div>
          ) : (
            <MessageFeed
              messages={messages}
              loading={loading}
              activeCitation={activeCitation}
              setActiveCitation={setActiveCitation}
            />
          )}
        </div>

        {/* BOTTOM INPUT PILLED FORM */}
        <ChatInput
          input={input}
          setInput={setInput}
          loading={loading}
          onSubmit={handleSubmitQuery}
        />
      </main>
    </div>
  )
}

export default App
