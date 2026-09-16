import React, { useState, useEffect } from 'react'
import { FileText, Upload, X, CheckCircle, AlertCircle, Loader2, Database } from 'lucide-react'

interface DocumentMetadata {
  filename: string
  title?: string
  chunks_count: number
}

interface DocumentModalProps {
  isOpen: boolean
  onClose: () => void
  apiBaseUrl: string
}

export const DocumentModal: React.FC<DocumentModalProps> = ({ isOpen, onClose, apiBaseUrl }) => {
  const [documents, setDocuments] = useState<DocumentMetadata[]>([])
  const [loading, setLoading] = useState(false)
  const [uploading, setUploading] = useState(false)
  const [uploadStatus, setUploadStatus] = useState<{ type: 'success' | 'error'; message: string } | null>(null)
  const [dragActive, setDragActive] = useState(false)

  const fetchDocuments = React.useCallback(async () => {
    setLoading(true)
    try {
      const res = await fetch(`${apiBaseUrl}/documents`)
      if (res.ok) {
        const data = await res.json()
        setDocuments(data.documents || [])
      }
    } catch (err) {
      console.error('Failed to load documents:', err)
    } finally {
      setLoading(false)
    }
  }, [apiBaseUrl])

  useEffect(() => {
    if (isOpen) {
      fetchDocuments()
      setUploadStatus(null)
    }
  }, [isOpen, fetchDocuments])

  const handleFileUpload = async (file: File) => {
    if (!file.name.endsWith('.pdf')) {
      setUploadStatus({ type: 'error', message: 'Only PDF documents are supported.' })
      return
    }

    setUploading(true)
    setUploadStatus(null)

    const formData = new FormData()
    formData.append('file', file)

    try {
      const res = await fetch(`${apiBaseUrl}/documents/upload`, {
        method: 'POST',
        body: formData,
      })

      const data = await res.json()

      if (res.ok) {
        setUploadStatus({
          type: 'success',
          message: `Successfully ingested "${file.name}" into RAG memory (${data.chunks_count} chunks created).`,
        })
        fetchDocuments()
      } else {
        setUploadStatus({ type: 'error', message: data.detail || 'Failed to upload document.' })
      }
    } catch {
      setUploadStatus({ type: 'error', message: 'Network error uploading file.' })
    } finally {
      setUploading(false)
    }
  }

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault()
    setDragActive(false)
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFileUpload(e.dataTransfer.files[0])
    }
  }

  if (!isOpen) return null

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-container" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <div className="modal-title-row">
            <div className="modal-icon-badge">
              <Database size={18} />
            </div>
            <div>
              <h3>RAG Knowledge Base & Documents</h3>
              <p>Upload SOPs, policies, or financial reports for instant AI retrieval.</p>
            </div>
          </div>
          <button className="icon-close-btn" onClick={onClose}>
            <X size={18} />
          </button>
        </div>

        <div className="modal-body">
          {/* Upload Drop Zone */}
          <div
            className={`upload-dropzone ${dragActive ? 'active' : ''}`}
            onDragOver={(e) => {
              e.preventDefault()
              setDragActive(true)
            }}
            onDragLeave={() => setDragActive(false)}
            onDrop={handleDrop}
          >
            <div className="dropzone-icon">
              {uploading ? <Loader2 size={24} className="spin" /> : <Upload size={24} />}
            </div>
            <div className="dropzone-text">
              <p className="dropzone-title">
                {uploading ? 'Processing & Embedding PDF...' : 'Drag & drop your PDF file here'}
              </p>
              <p className="dropzone-sub">Supports PDF documents for RAG semantic search</p>
            </div>
            <label className="btn-upload-browse">
              Browse File
              <input
                type="file"
                accept=".pdf"
                style={{ display: 'none' }}
                onChange={(e) => {
                  if (e.target.files && e.target.files[0]) {
                    handleFileUpload(e.target.files[0])
                  }
                }}
                disabled={uploading}
              />
            </label>
          </div>

          {/* Status Message */}
          {uploadStatus && (
            <div className={`status-banner ${uploadStatus.type}`}>
              {uploadStatus.type === 'success' ? <CheckCircle size={16} /> : <AlertCircle size={16} />}
              <span>{uploadStatus.message}</span>
            </div>
          )}

          {/* Document List */}
          <div className="doc-section">
            <h4 className="doc-section-title">Indexed Knowledge Base Documents ({documents.length})</h4>
            {loading ? (
              <div className="doc-loading">
                <Loader2 size={20} className="spin" />
                <span>Loading RAG documents...</span>
              </div>
            ) : documents.length > 0 ? (
              <div className="doc-grid">
                {documents.map((doc, idx) => (
                  <div key={idx} className="doc-card">
                    <div className="doc-card-icon">
                      <FileText size={20} />
                    </div>
                    <div className="doc-card-info">
                      <div className="doc-name" title={doc.filename}>{doc.title || doc.filename}</div>
                      <div className="doc-meta">{doc.chunks_count} vector chunks indexed</div>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="doc-empty">No documents uploaded yet. Upload a PDF above to enable document search!</div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
