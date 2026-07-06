import React, { useState } from 'react'
import { Table2, ChevronDown, ChevronRight } from 'lucide-react'

export interface ColumnSchema {
  name: string
  type: string
}

export interface TableSchema {
  name: string
  description: string
  columns: ColumnSchema[]
}

interface SchemaExplorerProps {
  schemaData: TableSchema[]
}

export const SchemaExplorer: React.FC<SchemaExplorerProps> = ({ schemaData }) => {
  const [expandedTable, setExpandedTable] = useState<string | null>(null)

  const handleTableToggle = (tableName: string) => {
    setExpandedTable(prev => (prev === tableName ? null : tableName))
  }

  return (
    <div className="schema-explorer" role="region" aria-label="Database Schema Explorer">
      {schemaData.map(table => {
        const isExpanded = expandedTable === table.name
        return (
          <div key={table.name} className="schema-table-card">
            <button
              className={`schema-table-trigger ${isExpanded ? 'active' : ''}`}
              onClick={() => handleTableToggle(table.name)}
              aria-expanded={isExpanded}
              aria-controls={`schema-table-panel-${table.name}`}
              aria-label={`Table ${table.name}: ${table.description}`}
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px', overflow: 'hidden' }}>
                <Table2 size={13} className="table-card-icon" aria-hidden="true" />
                <span className="table-name-text">{table.name}</span>
              </div>
              {isExpanded ? (
                <ChevronDown size={12} aria-hidden="true" />
              ) : (
                <ChevronRight size={12} aria-hidden="true" />
              )}
            </button>
            {isExpanded && (
              <div
                id={`schema-table-panel-${table.name}`}
                className="schema-table-details"
                role="region"
                aria-label={`${table.name} details`}
              >
                <p className="schema-table-desc">{table.description}</p>
                <div className="schema-column-list" role="list">
                  {table.columns.map(col => (
                    <div key={col.name} className="schema-column-item" role="listitem">
                      <span className="column-name">{col.name}</span>
                      <span className="column-type">{col.type}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )
      })}
    </div>
  )
}
