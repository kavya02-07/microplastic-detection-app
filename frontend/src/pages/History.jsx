import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import DashboardLayout from '../components/DashboardLayout';
import DetectionResults from '../components/DetectionResults';
import { analysesAPI } from '../services/api';
import { useAuth } from '../context/AuthContext';

export default function History() {
  const { id: urlAnalysisId } = useParams();
  const navigate = useNavigate();
  const { logout } = useAuth();

  const [analyses, setAnalyses] = useState([]);
  const [selectedAnalysis, setSelectedAnalysis] = useState(null);
  const [loadingList, setLoadingList] = useState(true);
  const [loadingDetail, setLoadingDetail] = useState(false);
  const [errorMessage, setErrorMessage] = useState(null);

  // Fetch list of analyses for the authenticated user
  const fetchAnalysesList = async () => {
    setLoadingList(true);
    setErrorMessage(null);
    try {
      const data = await analysesAPI.list();
      setAnalyses(data || []);
    } catch (err) {
      console.error('Failed to load analyses history:', err);
      if (err.status === 401) {
        logout();
        navigate('/login');
        return;
      }
      setErrorMessage(
        err.message || 'Failed to retrieve analysis history. Please check your connection and try again.'
      );
    } finally {
      setLoadingList(false);
    }
  };

  // Fetch a single historical analysis by ID (does NOT rerun YOLO)
  const fetchAnalysisDetail = async (analysisId) => {
    setLoadingDetail(true);
    setErrorMessage(null);
    try {
      const data = await analysesAPI.getById(analysisId);
      setSelectedAnalysis(data);
    } catch (err) {
      console.error(`Failed to load historical analysis #${analysisId}:`, err);
      if (err.status === 401) {
        logout();
        navigate('/login');
        return;
      }
      setErrorMessage(
        err.status === 404
          ? `Analysis #${analysisId} was not found.`
          : err.status === 403
          ? `You do not have permission to view analysis #${analysisId}.`
          : err.message || `Failed to load details for analysis #${analysisId}.`
      );
      setSelectedAnalysis(null);
    } finally {
      setLoadingDetail(false);
    }
  };

  useEffect(() => {
    fetchAnalysesList();
  }, []);

  useEffect(() => {
    if (urlAnalysisId) {
      fetchAnalysisDetail(urlAnalysisId);
    } else {
      setSelectedAnalysis(null);
    }
  }, [urlAnalysisId]);

  const handleSelectAnalysis = (analysisId) => {
    navigate(`/history/${analysisId}`);
  };

  const handleBackToList = () => {
    setSelectedAnalysis(null);
    navigate('/history');
  };

  const formatTimestamp = (dateStr) => {
    if (!dateStr) return '—';
    try {
      const d = new Date(dateStr);
      return d.toLocaleString(undefined, {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
      });
    } catch {
      return dateStr;
    }
  };

  return (
    <DashboardLayout activeTab="history">
      <div className="history-page-container">
        {/* Header Banner */}
        <div className="history-header-banner">
          <div>
            <h2>Analysis History & Audit Log</h2>
            <p>
              Review previously computed aquatic sample analyses stored securely in SQLite database.
            </p>
          </div>
          <div className="history-meta-badge">
            <span className="badge-pulse-dot"></span>
            {analyses.length} Saved {analyses.length === 1 ? 'Record' : 'Records'}
          </div>
        </div>

        {/* Error Alert Box */}
        {errorMessage && (
          <div className="alert alert-error">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <circle cx="12" cy="12" r="10"></circle>
              <line x1="12" y1="8" x2="12" y2="12"></line>
              <line x1="12" y1="16" x2="12.01" y2="16"></line>
            </svg>
            <div className="alert-text">
              <strong>Error:</strong> {errorMessage}
            </div>
            <button
              type="button"
              className="alert-close-btn"
              onClick={() => setErrorMessage(null)}
            >
              ×
            </button>
          </div>
        )}

        {/* View Detail Mode */}
        {loadingDetail ? (
          <div className="history-loading-box">
            <div className="spinner"></div>
            <p>Retrieving saved analysis #{urlAnalysisId} from database...</p>
            <span className="loading-sub">No AI re-inference required</span>
          </div>
        ) : selectedAnalysis ? (
          <div className="historical-detail-wrapper">
            <div className="detail-navigation-bar">
              <button
                type="button"
                className="btn-back-link"
                onClick={handleBackToList}
              >
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <line x1="19" y1="12" x2="5" y2="12"></line>
                  <polyline points="12 19 5 12 12 5"></polyline>
                </svg>
                Back to All Historical Analyses
              </button>
              <span className="record-status-pill">
                Record #{selectedAnalysis.id} • Static Audit Data
              </span>
            </div>

            <DetectionResults
              results={selectedAnalysis}
              isHistorical={true}
              onBackToHistory={handleBackToList}
            />
          </div>
        ) : loadingList ? (
          /* Loading List State */
          <div className="history-loading-box">
            <div className="spinner"></div>
            <p>Loading historical analysis logs...</p>
          </div>
        ) : analyses.length === 0 ? (
          /* Empty History State */
          <div className="history-empty-card">
            <div className="empty-state-icon">📋</div>
            <h3>No Previous Analyses Found</h3>
            <p>
              You haven&apos;t processed any aquatic samples yet. Run an analysis using our YOLOv8 model to automatically persist your results and access historical records anytime.
            </p>
            <button
              type="button"
              className="btn-primary"
              style={{ maxWidth: '220px', marginTop: '1rem' }}
              onClick={() => navigate('/analyze')}
            >
              Analyze Your First Sample
            </button>
          </div>
        ) : (
          /* History Table List */
          <div className="history-table-wrapper">
            <div className="table-top-bar">
              <div>
                <h4 className="table-title">Saved Analysis Records</h4>
                <p className="table-subtitle">
                  Showing {analyses.length} aquatic sample {analyses.length === 1 ? 'run' : 'runs'} associated with your researcher account
                </p>
              </div>
              <button
                type="button"
                className="btn-refresh-history"
                onClick={fetchAnalysesList}
                title="Refresh history list"
              >
                <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <polyline points="23 4 23 10 17 10"></polyline>
                  <polyline points="1 20 1 14 7 14"></polyline>
                  <path d="M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15"></path>
                </svg>
                Refresh
              </button>
            </div>

            <div className="table-responsive">
              <table className="history-table">
                <thead>
                  <tr>
                    <th>Record ID</th>
                    <th>Sample Image</th>
                    <th>Total Particles</th>
                    <th>Average Confidence</th>
                    <th>Inference Time</th>
                    <th>Analysis Date</th>
                    <th style={{ textAlign: 'right' }}>Action</th>
                  </tr>
                </thead>
                <tbody>
                  {analyses.map((item) => (
                    <tr key={item.id} className="history-table-row">
                      <td className="mono-col record-id-col">
                        <span className="record-hash">#</span>
                        <strong>{item.id}</strong>
                      </td>
                      <td>
                        <div className="file-info-cell">
                          <span className="file-icon">🖼️</span>
                          <span className="file-name" title={item.original_filename}>
                            {item.original_filename}
                          </span>
                        </div>
                      </td>
                      <td>
                        <span className="particles-badge">
                          <strong>{item.total_detections}</strong> particles
                        </span>
                      </td>
                      <td className="mono-col">
                        <span className="conf-value">
                          {item.average_confidence != null
                            ? (item.average_confidence * 100).toFixed(1) + '%'
                            : '—'}
                        </span>
                      </td>
                      <td className="mono-col latency-col">
                        {item.inference_time_ms != null
                          ? item.inference_time_ms > 1000
                            ? (item.inference_time_ms / 1000).toFixed(2) + ' s'
                            : item.inference_time_ms.toFixed(1) + ' ms'
                          : '—'}
                      </td>
                      <td className="date-col">
                        {formatTimestamp(item.created_at)}
                      </td>
                      <td style={{ textAlign: 'right' }}>
                        <button
                          type="button"
                          className="btn-view-analysis"
                          onClick={() => handleSelectAnalysis(item.id)}
                          title={`View full report for analysis #${item.id}`}
                        >
                          <span>View Analysis</span>
                          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                            <polyline points="9 18 15 12 9 6"></polyline>
                          </svg>
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </div>
    </DashboardLayout>
  );
}
