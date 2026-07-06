import React, { useState } from 'react'
import { BarChart3, Table2 } from 'lucide-react'
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

interface SqlResultsWidgetProps {
  results: Record<string, unknown>[]
}

export const SqlResultsWidget: React.FC<SqlResultsWidgetProps> = ({ results }) => {
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
    <div className="chart-card" role="region" aria-label="Database query results widget">
      <div className="widget-header">
        <span className="widget-title">
          {viewType === 'area' && (
            <>
              <BarChart3 size={15} className="widget-title-icon" aria-hidden="true" />
              Visualized Trend Line
            </>
          )}
          {viewType === 'bar' && (
            <>
              <BarChart3 size={15} className="widget-title-icon" aria-hidden="true" />
              Relevance Bar Comparison (Top 5)
            </>
          )}
          {viewType === 'table' && (
            <>
              <Table2 size={15} className="widget-title-icon" aria-hidden="true" />
              Database Records ({results.length} rows)
            </>
          )}
        </span>
        <div className="widget-controls" role="tablist" aria-label="Result display views">
          {canPlot && (
            <>
              <button
                role="tab"
                aria-selected={viewType === 'area'}
                className={`toggle-btn ${viewType === 'area' ? 'active' : ''}`}
                onClick={() => setViewType('area')}
              >
                Line
              </button>
              <button
                role="tab"
                aria-selected={viewType === 'bar'}
                className={`toggle-btn ${viewType === 'bar' ? 'active' : ''}`}
                onClick={() => setViewType('bar')}
              >
                Bar
              </button>
            </>
          )}
          <button
            role="tab"
            aria-selected={viewType === 'table'}
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
