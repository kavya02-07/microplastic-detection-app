import { useState, useEffect, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import DashboardLayout from '../components/DashboardLayout';
import { analysesAPI, reportsAPI } from '../services/api';
import { useAuth } from '../context/AuthContext';

export default function Reports() {
  const navigate = useNavigate();
  const { logout } = useAuth();

  const [analyses, setAnalyses] = useState([]);
  const [selectedAnalysis, setSelectedAnalysis] = useState(null);
  const [detailData, setDetailData] = useState(null);
  const [loadingList, setLoadingList] = useState(true);
  const [loadingDetail, setLoadingDetail] = useState(false);
  const [downloading, setDownloading] = useState(false);
  const [errorMessage, setErrorMessage] = useState(null);

  // Fetch list of analyses
  const fetchAnalyses = async () => {
    setLoadingList(true);
    setErrorMessage(null);
    try {
      const data = await analysesAPI.list();
      setAnalyses(data || []);
    } catch (err) {
      if (err.status === 401) { logout(); navigate('/login'); return; }
      setErrorMessage(err.message || 'Failed to load analyses.');
    } finally {
      setLoadingList(false);
    }
  };

  // Fetch single analysis with detections for preview
  const fetchDetail = async (analysisId) => {
    setLoadingDetail(true);
    setErrorMessage(null);
    try {
      const data = await analysesAPI.getById(analysisId);
      setDetailData(data);
    } catch (err) {
      if (err.status === 401) { logout(); navigate('/login'); return; }
      setErrorMessage(err.message || 'Failed to load analysis details.');
      setDetailData(null);
    } finally {
      setLoadingDetail(false);
    }
  };

  useEffect(() => { fetchAnalyses(); }, []);

  const handleSelectAnalysis = (analysis) => {
    setSelectedAnalysis(analysis);
    fetchDetail(analysis.id);
  };

  const handleBackToList = () => {
    setSelectedAnalysis(null);
    setDetailData(null);
  };

  const handleDownloadPDF = async () => {
    if (!selectedAnalysis) return;
    setDownloading(true);
    setErrorMessage(null);
    try {
      const blob = await reportsAPI.downloadReport(selectedAnalysis.id);
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `microplastic_report_${selectedAnalysis.id}.pdf`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    } catch (err) {
      if (err.status === 401) { logout(); navigate('/login'); return; }
      setErrorMessage(err.message || 'Failed to generate report.');
    } finally {
      setDownloading(false);
    }
  };

  // ─── Derived analytics for preview ───────────────────────────────────
  const analytics = useMemo(() => {
    if (!detailData || !detailData.detections) return null;
    const dets = detailData.detections;
    const total = dets.length;
    if (total === 0) return { total: 0, classes: {}, confidences: [], areas: [] };

    const classes = {};
    const allClasses = ['Fibers', 'Films', 'Fragments', 'Pellets'];
    allClasses.forEach(c => { classes[c] = { count: 0, areas: [], widths: [], heights: [], ars: [], confs: [] }; });

    const confidences = [];
    const areas = [];

    dets.forEach(d => {
      if (d.confidence != null) confidences.push(d.confidence);
      if (d.area != null) areas.push(d.area);
      const cls = classes[d.class_name];
      if (cls) {
        cls.count++;
        if (d.area != null) cls.areas.push(d.area);
        if (d.width != null) cls.widths.push(d.width);
        if (d.height != null) cls.heights.push(d.height);
        if (d.aspect_ratio != null) cls.ars.push(d.aspect_ratio);
        if (d.confidence != null) cls.confs.push(d.confidence);
      }
    });

    const mean = arr => arr.length ? arr.reduce((a, b) => a + b, 0) / arr.length : null;
    const median = arr => {
      if (!arr.length) return null;
      const s = [...arr].sort((a, b) => a - b);
      const mid = Math.floor(s.length / 2);
      return s.length % 2 ? s[mid] : (s[mid - 1] + s[mid]) / 2;
    };
    const stdev = arr => {
      if (arr.length < 2) return null;
      const m = mean(arr);
      return Math.sqrt(arr.reduce((sum, v) => sum + (v - m) ** 2, 0) / (arr.length - 1));
    };

    return {
      total,
      classes,
      confidences,
      areas,
      confStats: {
        mean: mean(confidences),
        median: median(confidences),
        min: confidences.length ? Math.min(...confidences) : null,
        max: confidences.length ? Math.max(...confidences) : null,
        stdev: stdev(confidences),
      },
      areaStats: {
        mean: mean(areas),
        median: median(areas),
        min: areas.length ? Math.min(...areas) : null,
        max: areas.length ? Math.max(...areas) : null,
      },
    };
  }, [detailData]);

  const fmt = (val, dec = 2) => (val != null ? val.toFixed(dec) : '—');
  const pct = (count, total) => total > 0 ? ((count / total) * 100).toFixed(1) + '%' : '0.0%';

  const formatTimestamp = (dateStr) => {
    if (!dateStr) return '—';
    try {
      return new Date(dateStr).toLocaleString(undefined, {
        year: 'numeric', month: 'short', day: 'numeric',
        hour: '2-digit', minute: '2-digit',
      });
    } catch { return dateStr; }
  };

  return (
    <DashboardLayout activeTab="reports">
      <div className="reports-page-container">
        {/* Header */}
        <div className="reports-header-banner">
          <div>
            <h2>Analytical Reports</h2>
            <p>Generate comprehensive PDF reports from your saved microplastic analyses.</p>
          </div>
          <div className="reports-meta-badge">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>
              <polyline points="14 2 14 8 20 8"></polyline>
            </svg>
            {analyses.length} Available {analyses.length === 1 ? 'Analysis' : 'Analyses'}
          </div>
        </div>

        {/* Error */}
        {errorMessage && (
          <div className="alert alert-error">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <circle cx="12" cy="12" r="10"></circle>
              <line x1="12" y1="8" x2="12" y2="12"></line>
              <line x1="12" y1="16" x2="12.01" y2="16"></line>
            </svg>
            <div className="alert-text"><strong>Error:</strong> {errorMessage}</div>
            <button type="button" className="alert-close-btn" onClick={() => setErrorMessage(null)}>×</button>
          </div>
        )}

        {/* Detail / Preview Mode */}
        {selectedAnalysis && (loadingDetail ? (
          <div className="reports-loading-box">
            <div className="spinner"></div>
            <p>Loading analysis data for report preview...</p>
          </div>
        ) : detailData && analytics ? (
          <div className="report-preview-container">
            {/* Nav bar */}
            <div className="report-preview-nav">
              <button type="button" className="btn-back-link" onClick={handleBackToList}>
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <line x1="19" y1="12" x2="5" y2="12"></line>
                  <polyline points="12 19 5 12 12 5"></polyline>
                </svg>
                Back to Analysis List
              </button>
              <button
                type="button"
                className="btn-primary btn-download-report"
                onClick={handleDownloadPDF}
                disabled={downloading}
              >
                {downloading ? (
                  <>
                    <div className="spinner-sm"></div>
                    Generating PDF...
                  </>
                ) : (
                  <>
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                      <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>
                      <polyline points="7 10 12 15 17 10"></polyline>
                      <line x1="12" y1="15" x2="12" y2="3"></line>
                    </svg>
                    Download PDF Report
                  </>
                )}
              </button>
            </div>

            {/* Report Preview Header */}
            <div className="report-preview-header">
              <h3>Report Preview — Analysis #{detailData.id}</h3>
              <span className="report-preview-file">{detailData.original_filename}</span>
            </div>

            {/* Executive Summary Card */}
            <div className="report-section-card">
              <h4 className="report-section-title">Executive Summary</h4>
              <p className="report-section-text">
                Analysis <strong>#{detailData.id}</strong> of sample <strong>{detailData.original_filename}</strong> detected{' '}
                <strong>{analytics.total}</strong> particle{analytics.total !== 1 ? 's' : ''} across{' '}
                {Object.values(analytics.classes).filter(c => c.count > 0).length} morphological class{Object.values(analytics.classes).filter(c => c.count > 0).length !== 1 ? 'es' : ''}.
                Average confidence: <strong>{fmt(detailData.average_confidence * 100, 1)}%</strong>.
                Inference time: <strong>{fmt(detailData.inference_time_ms, 1)} ms</strong>.
              </p>
            </div>

            {/* Morphology Composition */}
            <div className="report-section-card">
              <h4 className="report-section-title">Morphology Composition</h4>
              <div className="report-morph-grid">
                {['Fibers', 'Films', 'Fragments', 'Pellets'].map(cls => {
                  const data = analytics.classes[cls];
                  const count = data ? data.count : 0;
                  return (
                    <div key={cls} className={`report-morph-card ${count > 0 ? 'active' : ''}`}>
                      <div className="morph-card-class">{cls}</div>
                      <div className="morph-card-count">{count}</div>
                      <div className="morph-card-pct">{pct(count, analytics.total)}</div>
                    </div>
                  );
                })}
              </div>
              {/* Visual bar */}
              {analytics.total > 0 && (
                <div className="morph-bar-container">
                  {['Fibers', 'Films', 'Fragments', 'Pellets'].map(cls => {
                    const count = analytics.classes[cls]?.count || 0;
                    if (count === 0) return null;
                    const widthPct = (count / analytics.total) * 100;
                    return (
                      <div
                        key={cls}
                        className={`morph-bar-segment morph-${cls.toLowerCase()}`}
                        style={{ width: `${widthPct}%` }}
                        title={`${cls}: ${count} (${widthPct.toFixed(1)}%)`}
                      ></div>
                    );
                  })}
                </div>
              )}
            </div>

            {/* Confidence Statistics */}
            <div className="report-section-card">
              <h4 className="report-section-title">Confidence Statistics</h4>
              {analytics.confidences.length > 0 ? (
                <div className="report-stats-grid">
                  <div className="stat-item">
                    <span className="stat-label">Mean</span>
                    <span className="stat-value">{fmt(analytics.confStats.mean, 4)}</span>
                  </div>
                  <div className="stat-item">
                    <span className="stat-label">Median</span>
                    <span className="stat-value">{fmt(analytics.confStats.median, 4)}</span>
                  </div>
                  <div className="stat-item">
                    <span className="stat-label">Min</span>
                    <span className="stat-value">{fmt(analytics.confStats.min, 4)}</span>
                  </div>
                  <div className="stat-item">
                    <span className="stat-label">Max</span>
                    <span className="stat-value">{fmt(analytics.confStats.max, 4)}</span>
                  </div>
                  <div className="stat-item">
                    <span className="stat-label">Range</span>
                    <span className="stat-value">
                      {analytics.confStats.min != null && analytics.confStats.max != null
                        ? fmt(analytics.confStats.max - analytics.confStats.min, 4)
                        : '—'}
                    </span>
                  </div>
                  <div className="stat-item">
                    <span className="stat-label">Std Dev</span>
                    <span className="stat-value">{fmt(analytics.confStats.stdev, 4)}</span>
                  </div>
                </div>
              ) : (
                <p className="report-no-data">No confidence data available.</p>
              )}
            </div>

            {/* Morphometry Summary */}
            <div className="report-section-card">
              <h4 className="report-section-title">Morphometry Summary</h4>
              <p className="report-note">Image-space pixel measurements from bounding boxes.</p>
              {analytics.areas.length > 0 ? (
                <table className="report-table">
                  <thead>
                    <tr>
                      <th>Metric</th><th>Mean</th><th>Median</th><th>Min</th><th>Max</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr>
                      <td>Area (px²)</td>
                      <td>{fmt(analytics.areaStats.mean)}</td>
                      <td>{fmt(analytics.areaStats.median)}</td>
                      <td>{fmt(analytics.areaStats.min)}</td>
                      <td>{fmt(analytics.areaStats.max)}</td>
                    </tr>
                  </tbody>
                </table>
              ) : (
                <p className="report-no-data">No morphometric data available.</p>
              )}
            </div>

            {/* Class-Wise Morphometry */}
            <div className="report-section-card">
              <h4 className="report-section-title">Class-Wise Morphometry</h4>
              <table className="report-table">
                <thead>
                  <tr>
                    <th>Class</th><th>Count</th><th>%</th><th>Avg Area</th><th>Avg Width</th><th>Avg Height</th><th>Avg AR</th>
                  </tr>
                </thead>
                <tbody>
                  {['Fibers', 'Films', 'Fragments', 'Pellets'].map(cls => {
                    const d = analytics.classes[cls];
                    if (!d || d.count === 0) return null;
                    const mean = arr => arr.length ? arr.reduce((a, b) => a + b, 0) / arr.length : null;
                    return (
                      <tr key={cls}>
                        <td>{cls}</td>
                        <td>{d.count}</td>
                        <td>{pct(d.count, analytics.total)}</td>
                        <td>{fmt(mean(d.areas))}</td>
                        <td>{fmt(mean(d.widths))}</td>
                        <td>{fmt(mean(d.heights))}</td>
                        <td>{fmt(mean(d.ars))}</td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>

            {/* Quantitative Summary */}
            <div className="report-section-card">
              <h4 className="report-section-title">Quantitative Summary</h4>
              <div className="report-quant-grid">
                <div className="quant-item">
                  <span className="quant-label">Total Particles</span>
                  <span className="quant-value">{analytics.total}</span>
                </div>
                <div className="quant-item">
                  <span className="quant-label">Classes Present</span>
                  <span className="quant-value">{Object.values(analytics.classes).filter(c => c.count > 0).length}</span>
                </div>
                <div className="quant-item">
                  <span className="quant-label">Dominant Class</span>
                  <span className="quant-value">
                    {analytics.total > 0
                      ? Object.entries(analytics.classes).sort((a, b) => b[1].count - a[1].count)[0][0]
                      : 'N/A'}
                  </span>
                </div>
                <div className="quant-item">
                  <span className="quant-label">Avg Confidence</span>
                  <span className="quant-value">{fmt(detailData.average_confidence * 100, 1)}%</span>
                </div>
                <div className="quant-item">
                  <span className="quant-label">Inference Time</span>
                  <span className="quant-value">{fmt(detailData.inference_time_ms, 1)} ms</span>
                </div>
                <div className="quant-item">
                  <span className="quant-label">Mean Area (px²)</span>
                  <span className="quant-value">{fmt(analytics.areaStats.mean)}</span>
                </div>
              </div>
            </div>

            {/* PDF info */}
            <div className="report-pdf-info">
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <circle cx="12" cy="12" r="10"></circle>
                <line x1="12" y1="16" x2="12" y2="12"></line>
                <line x1="12" y1="8" x2="12.01" y2="8"></line>
              </svg>
              <span>
                The downloadable PDF report includes additional sections: confidence distribution chart,
                particle area distribution chart, full detection appendix, methodology, model information,
                limitations, and conclusion.
              </span>
            </div>
          </div>
        ) : null)}

        {/* Analysis Selection List */}
        {!selectedAnalysis && (loadingList ? (
          <div className="reports-loading-box">
            <div className="spinner"></div>
            <p>Loading your analyses...</p>
          </div>
        ) : analyses.length === 0 ? (
          <div className="reports-empty-card">
            <div className="empty-state-icon">📋</div>
            <h3>No Analyses Available</h3>
            <p>Run an analysis first to generate reports from your results.</p>
            <button type="button" className="btn-primary" style={{ maxWidth: 220, marginTop: '1rem' }}
              onClick={() => navigate('/analyze')}>
              Analyze a Sample
            </button>
          </div>
        ) : (
          <div className="reports-list-wrapper">
            <div className="reports-list-header">
              <h4>Select an Analysis for Report</h4>
              <p>Choose a saved analysis to preview and download its PDF report.</p>
            </div>
            <div className="reports-card-grid">
              {analyses.map(item => (
                <div key={item.id} className="report-analysis-card" onClick={() => handleSelectAnalysis(item)}>
                  <div className="rac-top">
                    <span className="rac-id">#{item.id}</span>
                    <span className="rac-date">{formatTimestamp(item.created_at)}</span>
                  </div>
                  <div className="rac-filename" title={item.original_filename}>
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                      <rect x="3" y="3" width="18" height="18" rx="2" ry="2"></rect>
                      <circle cx="8.5" cy="8.5" r="1.5"></circle>
                      <polyline points="21 15 16 10 5 21"></polyline>
                    </svg>
                    {item.original_filename}
                  </div>
                  <div className="rac-stats">
                    <span className="rac-stat">
                      <strong>{item.total_detections}</strong> particles
                    </span>
                    <span className="rac-stat">
                      <strong>{item.average_confidence != null ? (item.average_confidence * 100).toFixed(1) : '—'}%</strong> conf
                    </span>
                    <span className="rac-stat">
                      <strong>{item.inference_time_ms != null ? item.inference_time_ms.toFixed(0) : '—'}</strong> ms
                    </span>
                  </div>
                  <div className="rac-action">
                    <span>View Report Preview</span>
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                      <polyline points="9 18 15 12 9 6"></polyline>
                    </svg>
                  </div>
                </div>
              ))}
            </div>
          </div>
        ))}
      </div>
    </DashboardLayout>
  );
}
