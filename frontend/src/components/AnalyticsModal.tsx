import React, { useState, useEffect } from 'react'
import { X, TrendingUp, DollarSign, Package, AlertTriangle, Loader2, BarChart3 } from 'lucide-react'
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  LineChart,
  Line
} from 'recharts'

interface AnalyticsReportData {
  sales: {
    total_revenue: number
    total_orders: number
    average_order_value: number
    top_selling_product?: string
  }
  inventory: {
    total_sku_count: number
    low_stock_items_count: number
    total_inventory_value: number
  }
  monthly_sales_distribution: Array<{ month: string; revenue: number; orders: number }>
  month_over_month_growth: Array<{ month: string; growth_percentage: number }>
}

interface AnalyticsModalProps {
  isOpen: boolean
  onClose: () => void
  apiBaseUrl: string
}

export const AnalyticsModal: React.FC<AnalyticsModalProps> = ({ isOpen, onClose, apiBaseUrl }) => {
  const [data, setData] = useState<AnalyticsReportData | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const fetchAnalytics = React.useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const res = await fetch(`${apiBaseUrl}/analytics/report`)
      if (res.ok) {
        const json = await res.json()
        setData(json)
      } else {
        setError('Failed to fetch analytics report from server.')
      }
    } catch {
      setError('Network error fetching analytics data.')
    } finally {
      setLoading(false)
    }
  }, [apiBaseUrl])

  useEffect(() => {
    if (isOpen) {
      fetchAnalytics()
    }
  }, [isOpen, fetchAnalytics])

  if (!isOpen) return null

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-container large" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <div className="modal-title-row">
            <div className="modal-icon-badge accent">
              <BarChart3 size={18} />
            </div>
            <div>
              <h3>Business Performance Analytics Overview</h3>
              <p>Real-time metrics, revenue trends, and inventory health calculated from the database.</p>
            </div>
          </div>
          <button className="icon-close-btn" onClick={onClose}>
            <X size={18} />
          </button>
        </div>

        <div className="modal-body">
          {loading ? (
            <div className="doc-loading" style={{ minHeight: '200px' }}>
              <Loader2 size={24} className="spin" />
              <span>Compiling business analytics report...</span>
            </div>
          ) : error ? (
            <div className="status-banner error">{error}</div>
          ) : data ? (
            <div className="analytics-content">
              {/* Top KPI Cards */}
              <div className="kpi-grid">
                <div className="kpi-card">
                  <div className="kpi-header">
                    <span className="kpi-label">Total Revenue</span>
                    <DollarSign size={16} className="kpi-icon" />
                  </div>
                  <div className="kpi-value">${data.sales.total_revenue?.toLocaleString() || '0'}</div>
                  <div className="kpi-sub">Avg Order: ${data.sales.average_order_value?.toFixed(2) || '0'}</div>
                </div>

                <div className="kpi-card">
                  <div className="kpi-header">
                    <span className="kpi-label">Total Orders</span>
                    <TrendingUp size={16} className="kpi-icon" />
                  </div>
                  <div className="kpi-value">{data.sales.total_orders?.toLocaleString() || '0'}</div>
                  <div className="kpi-sub">Top Product: {data.sales.top_selling_product || 'N/A'}</div>
                </div>

                <div className="kpi-card">
                  <div className="kpi-header">
                    <span className="kpi-label">Inventory Valuation</span>
                    <Package size={16} className="kpi-icon" />
                  </div>
                  <div className="kpi-value">${data.inventory.total_inventory_value?.toLocaleString() || '0'}</div>
                  <div className="kpi-sub">{data.inventory.total_sku_count || 0} active SKUs</div>
                </div>

                <div className="kpi-card">
                  <div className="kpi-header">
                    <span className="kpi-label">Low Stock Warnings</span>
                    <AlertTriangle size={16} className="kpi-icon warn" />
                  </div>
                  <div className="kpi-value warn">{data.inventory.low_stock_items_count || 0}</div>
                  <div className="kpi-sub">SKUs below safety threshold</div>
                </div>
              </div>

              {/* Monthly Revenue Chart */}
              {data.monthly_sales_distribution && data.monthly_sales_distribution.length > 0 && (
                <div className="analytics-chart-box">
                  <h4 className="chart-box-title">Monthly Revenue Distribution</h4>
                  <div style={{ width: '100%', height: 220 }}>
                    <ResponsiveContainer width="99%" height="100%">
                      <BarChart data={data.monthly_sales_distribution} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
                        <CartesianGrid strokeDasharray="3 3" stroke="var(--border-subtle)" />
                        <XAxis dataKey="month" tick={{ fill: 'var(--text-secondary)', fontSize: 11 }} stroke="var(--border-subtle)" />
                        <YAxis tick={{ fill: 'var(--text-secondary)', fontSize: 11 }} stroke="var(--border-subtle)" />
                        <Tooltip
                          contentStyle={{ backgroundColor: 'var(--bg-secondary)', borderColor: 'var(--border-subtle)', color: 'var(--text-primary)', borderRadius: 8 }}
                        />
                        <Bar dataKey="revenue" fill="var(--accent-gpt)" radius={[4, 4, 0, 0]} />
                      </BarChart>
                    </ResponsiveContainer>
                  </div>
                </div>
              )}

              {/* MoM Growth Chart */}
              {data.month_over_month_growth && data.month_over_month_growth.length > 0 && (
                <div className="analytics-chart-box">
                  <h4 className="chart-box-title">Month-over-Month Revenue Growth (%)</h4>
                  <div style={{ width: '100%', height: 200 }}>
                    <ResponsiveContainer width="99%" height="100%">
                      <LineChart data={data.month_over_month_growth} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
                        <CartesianGrid strokeDasharray="3 3" stroke="var(--border-subtle)" />
                        <XAxis dataKey="month" tick={{ fill: 'var(--text-secondary)', fontSize: 11 }} stroke="var(--border-subtle)" />
                        <YAxis tick={{ fill: 'var(--text-secondary)', fontSize: 11 }} stroke="var(--border-subtle)" />
                        <Tooltip
                          contentStyle={{ backgroundColor: 'var(--bg-secondary)', borderColor: 'var(--border-subtle)', color: 'var(--text-primary)', borderRadius: 8 }}
                        />
                        <Line type="monotone" dataKey="growth_percentage" stroke="#10a37f" strokeWidth={2} dot={{ fill: '#10a37f', r: 4 }} />
                      </LineChart>
                    </ResponsiveContainer>
                  </div>
                </div>
              )}
            </div>
          ) : null}
        </div>
      </div>
    </div>
  )
}
