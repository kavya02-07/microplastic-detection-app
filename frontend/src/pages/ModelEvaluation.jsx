import { useState, useEffect, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import DashboardLayout from '../components/DashboardLayout';
import { modelAPI } from '../services/api';
import { useAuth } from '../context/AuthContext';

// ─── Lightweight inline SVG line chart (no external chart dependency) ─────────
// Renders one or more series that share a y-axis, from real numeric arrays.
function LineChart({ title, series, xValues, yMin, yMax, yTicks = 4, yFormat }) {
  const W = 520;
  const H = 260;
  const padL = 52;
  const padR = 16;
  const padT = 16;
  const padB = 34;
  const plotW = W - padL - padR;
  const plotH = H - padT - padB;

  const allY = series.flatMap((s) => s.data).filter((v) => typeof v === 'number' && !isNaN(v));
  const dataMin = allY.length ? Math.min(...allY) : 0;
  const dataMax = allY.length ? Math.max(...allY) : 1;
  const lo = yMin != null ? yMin : dataMin;
  const hi = yMax != null ? yMax : dataMax;
  const span = hi - lo || 1;

  const n = xValues.length;
  const xAt = (i) => padL + (n <= 1 ? 0 : (i / (n - 1)) * plotW);
  const yAt = (v) => padT + plotH - ((v - lo) / span) * plotH;

  const fmtY = yFormat || ((v) => v.toFixed(2));
  const ticks = Array.from({ length: yTicks + 1 }, (_, k) => lo + (span * k) / yTicks);

  // x-axis reference labels (first, middle, last epoch)
  const xTickIdx = n > 1 ? [0, Math.floor((n - 1) / 2), n - 1] : [0];

  return (
    <div className="eval-chart-card">
      <h4 className="eval-chart-title">{title}</h4>
      <svg viewBox={`0 0 ${W} ${H}`} className="eval-chart-svg" role="img" aria-label={title}>
        {/* Y gridlines + labels */}
        {ticks.map((t, k) => (
          <g key={k}>
            <line x1={padL} y1={yAt(t)} x2={W - padR} y2={yAt(t)} stroke="#1e293b" strokeWidth="1" />
            <text x={padL - 8} y={yAt(t) + 3} textAnchor="end" fontSize="10" fill="#64748b">
              {fmtY(t)}
            </text>
          </g>
        ))}
        {/* X axis labels */}
        {xTickIdx.map((i) => (
          <text key={i} x={xAt(i)} y={H - padB + 18} textAnchor="middle" fontSize="10" fill="#64748b">
            {xValues[i]}
          </text>
        ))}
        <text x={padL + plotW / 2} y={H - 4} textAnchor="middle" fontSize="10" fill="#94a3b8">
          Epoch
        </text>
        {/* Series polylines */}
        {series.map((s) => {
          const pts = s.data
            .map((v, i) => (typeof v === 'number' && !isNaN(v) ? `${xAt(i)},${yAt(v)}` : null))
            .filter(Boolean)
            .join(' ');
          return (
            <polyline
              key={s.label}
              points={pts}
              fill="none"
              stroke={s.color}
              strokeWidth="2"
              strokeLinejoin="round"
              strokeLinecap="round"
            />
          );
        })}
      </svg>
      <div className="eval-chart-legend">
        {series.map((s) => (
          <span key={s.label} className="eval-legend-item">
            <span className="eval-legend-swatch" style={{ backgroundColor: s.color }}></span>
            {s.label}
          </span>
        ))}
      </div>
    </div>
  );
}

export default function ModelEvaluation() {
  const navigate = useNavigate();
  const { logout } = useAuth();

  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [errorMessage, setErrorMessage] = useState(null);

  useEffect(() => {
    let cancelled = false;
    const load = async () => {
      setLoading(true);
      setErrorMessage(null);
      try {
        const result = await modelAPI.getEvaluation();
        if (!cancelled) setData(result);
      } catch (err) {
        if (cancelled) return;
        if (err.status === 401) {
          logout();
          navigate('/login');
          return;
        }
        setErrorMessage(
          err.status === 503
            ? 'Model evaluation metrics have not been extracted yet on the server.'
            : err.message || 'Failed to load model evaluation metrics.'
        );
      } finally {
        if (!cancelled) setLoading(false);
      }
    };
    load();
    return () => { cancelled = true; };
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  const charts = useMemo(() => {
    if (!data?.epoch_history) return null;
    const h = data.epoch_history;
    const epochs = h['epoch'] || [];
    const sum3 = (a, b, c) =>
      (a || []).map((v, i) => (v ?? 0) + (b?.[i] ?? 0) + (c?.[i] ?? 0));
    return {
      epochs,
      trainLoss: sum3(h['train/box_loss'], h['train/cls_loss'], h['train/dfl_loss']),
      valLoss: sum3(h['val/box_loss'], h['val/cls_loss'], h['val/dfl_loss']),
      map50: h['metrics/mAP50(B)'] || [],
      map5095: h['metrics/mAP50-95(B)'] || [],
      precision: h['metrics/precision(B)'] || [],
      recall: h['metrics/recall(B)'] || [],
    };
  }, [data]);

  const formatDate = (dateStr) => {
    if (!dateStr) return '—';
    try {
      return new Date(dateStr).toLocaleDateString(undefined, {
        year: 'numeric', month: 'long', day: 'numeric',
      });
    } catch { return dateStr; }
  };

  const asPct = (v) => (typeof v === 'number' ? (v * 100).toFixed(2) + '%' : '—');

  const fv = data?.final_validation_metrics || {};
  const cfg = data?.training_config || {};
  const model = data?.model || {};

  return (
    <DashboardLayout activeTab="model-evaluation">
      <div className="eval-page-container">
        {/* Header */}
        <div className="eval-header-banner">
          <div>
            <h2>Model Evaluation &amp; Research</h2>
            <p>
              Embedded training-run evaluation evidence for the deployed detection checkpoint.
            </p>
          </div>
          <div className="eval-evidence-chip">
            <span className="chip-dot"></span>
            Evidence: Training-run validation
          </div>
        </div>

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

        {loading ? (
          <div className="eval-loading-box">
            <div className="spinner"></div>
            <p>Loading embedded model evaluation metrics...</p>
          </div>
        ) : data ? (
          <>
            {/* 1. Model Information */}
            <section className="eval-section">
              <div className="section-heading-row">
                <h4 className="section-title-label">Model Information</h4>
                <span className="section-caption-label">Deployed detection checkpoint</span>
              </div>
              <div className="eval-info-grid">
                <div className="eval-info-item">
                  <span className="eval-info-label">Architecture</span>
                  <span className="eval-info-value">{model.architecture || '—'}</span>
                </div>
                <div className="eval-info-item">
                  <span className="eval-info-label">Deployed Checkpoint</span>
                  <span className="eval-info-value mono">{model.deployed_checkpoint || '—'}</span>
                </div>
                <div className="eval-info-item">
                  <span className="eval-info-label">Morphology Classes</span>
                  <span className="eval-info-value">
                    {model.num_classes != null ? `${model.num_classes} classes` : '—'}
                  </span>
                </div>
                <div className="eval-info-item">
                  <span className="eval-info-label">Checkpoint Date</span>
                  <span className="eval-info-value">{formatDate(model.checkpoint_date)}</span>
                </div>
                <div className="eval-info-item">
                  <span className="eval-info-label">Framework</span>
                  <span className="eval-info-value">
                    {model.framework || '—'}
                    {model.ultralytics_version ? ` v${model.ultralytics_version}` : ''}
                  </span>
                </div>
                <div className="eval-info-item">
                  <span className="eval-info-label">Class Names</span>
                  <span className="eval-info-value">
                    {model.class_names ? Object.values(model.class_names).join(', ') : '—'}
                  </span>
                </div>
              </div>
            </section>

            {/* 2. Validation Metrics */}
            <section className="eval-section">
              <div className="section-heading-row">
                <h4 className="section-title-label">Training-run Validation Metrics</h4>
                <span className="section-caption-label">Recorded in the deployed checkpoint</span>
              </div>
              <div className="eval-metrics-grid">
                <div className="eval-metric-card primary">
                  <span className="eval-metric-label">Precision</span>
                  <span className="eval-metric-value">{asPct(fv.precision)}</span>
                  <span className="eval-metric-key">metrics/precision(B)</span>
                </div>
                <div className="eval-metric-card">
                  <span className="eval-metric-label">Recall</span>
                  <span className="eval-metric-value">{asPct(fv.recall)}</span>
                  <span className="eval-metric-key">metrics/recall(B)</span>
                </div>
                <div className="eval-metric-card">
                  <span className="eval-metric-label">mAP@50</span>
                  <span className="eval-metric-value">{asPct(fv.map50)}</span>
                  <span className="eval-metric-key">metrics/mAP50(B)</span>
                </div>
                <div className="eval-metric-card">
                  <span className="eval-metric-label">mAP@50–95</span>
                  <span className="eval-metric-value">{asPct(fv.map50_95)}</span>
                  <span className="eval-metric-key">metrics/mAP50-95(B)</span>
                </div>
              </div>
              <p className="eval-metric-note">
                Aggregate (all-class) validation-split metrics from the original training run.
                Not independent test-set results.
              </p>
            </section>

            {/* 3. Training Configuration */}
            <section className="eval-section">
              <div className="section-heading-row">
                <h4 className="section-title-label">Training Configuration</h4>
                <span className="section-caption-label">Historical training metadata</span>
              </div>
              <div className="eval-info-grid">
                <div className="eval-info-item">
                  <span className="eval-info-label">Epochs</span>
                  <span className="eval-info-value">{cfg.epochs ?? '—'}</span>
                </div>
                <div className="eval-info-item">
                  <span className="eval-info-label">Image Size</span>
                  <span className="eval-info-value">{cfg.imgsz != null ? `${cfg.imgsz} px` : '—'}</span>
                </div>
                <div className="eval-info-item">
                  <span className="eval-info-label">Batch Size</span>
                  <span className="eval-info-value">{cfg.batch ?? '—'}</span>
                </div>
                <div className="eval-info-item">
                  <span className="eval-info-label">Optimizer</span>
                  <span className="eval-info-value">{cfg.optimizer ?? '—'}</span>
                </div>
                <div className="eval-info-item">
                  <span className="eval-info-label">Base Model</span>
                  <span className="eval-info-value mono">{cfg.base_model ?? '—'}</span>
                </div>
                <div className="eval-info-item">
                  <span className="eval-info-label">Task</span>
                  <span className="eval-info-value">{cfg.task ?? '—'}</span>
                </div>
              </div>
              <div className="eval-datasource-box">
                <span className="eval-datasource-label">Training Data Source</span>
                <span className="eval-datasource-path mono">{cfg.training_data_source || '—'}</span>
                <span className="eval-datasource-note">
                  Recorded training data source; dataset not included in this repository.
                </span>
              </div>
            </section>

            {/* 4. Training Curves */}
            {charts && (
              <section className="eval-section">
                <div className="section-heading-row">
                  <h4 className="section-title-label">Training Curves</h4>
                  <span className="section-caption-label">
                    {charts.epochs.length} epochs · recorded during training
                  </span>
                </div>
                <div className="eval-charts-grid">
                  <LineChart
                    title="Training vs Validation Loss (box + cls + dfl)"
                    xValues={charts.epochs}
                    yFormat={(v) => v.toFixed(1)}
                    series={[
                      { label: 'Train loss', color: '#06b6d4', data: charts.trainLoss },
                      { label: 'Validation loss', color: '#f59e0b', data: charts.valLoss },
                    ]}
                  />
                  <LineChart
                    title="mAP@50 over Epochs"
                    xValues={charts.epochs}
                    yMin={0}
                    yMax={1}
                    yFormat={(v) => v.toFixed(2)}
                    series={[{ label: 'mAP@50', color: '#10b981', data: charts.map50 }]}
                  />
                  <LineChart
                    title="mAP@50–95 over Epochs"
                    xValues={charts.epochs}
                    yMin={0}
                    yMax={1}
                    yFormat={(v) => v.toFixed(2)}
                    series={[{ label: 'mAP@50–95', color: '#8b5cf6', data: charts.map5095 }]}
                  />
                  <LineChart
                    title="Precision &amp; Recall over Epochs"
                    xValues={charts.epochs}
                    yMin={0}
                    yMax={1}
                    yFormat={(v) => v.toFixed(2)}
                    series={[
                      { label: 'Precision', color: '#0ea5e9', data: charts.precision },
                      { label: 'Recall', color: '#f43f5e', data: charts.recall },
                    ]}
                  />
                </div>
              </section>
            )}

            {/* 5. Evidence & Limitations */}
            <section className="eval-section">
              <div className="section-heading-row">
                <h4 className="section-title-label">Evidence &amp; Limitations</h4>
                <span className="section-caption-label">Transparency statement</span>
              </div>
              <div className="eval-limitations-box">
                <ul>
                  <li>
                    The metrics shown above are validation-split metrics recorded during the
                    original training run embedded in the deployed checkpoint.
                  </li>
                  <li>
                    The original training dataset is not included in this repository, so these
                    results cannot currently be independently reproduced here.
                  </li>
                  <li>
                    No independent held-out test set is available in the current repository.
                  </li>
                  <li>
                    No per-class precision, recall, mAP, or sample-level accuracy is claimed
                    because corresponding ground-truth labels are unavailable.
                  </li>
                  <li>
                    Individual uploaded-sample statistics such as detection count, confidence, and
                    inference time describe model output for that sample; they are not accuracy
                    measurements.
                  </li>
                </ul>
              </div>
            </section>

            {/* 6. Dataset / Ground Truth Status */}
            <section className="eval-section">
              <div className="section-heading-row">
                <h4 className="section-title-label">Dataset / Ground-Truth Status</h4>
                <span className="section-caption-label">Evidence availability</span>
              </div>
              <div className="eval-status-grid">
                <div className="eval-status-item">
                  <span className="eval-status-key">Dataset</span>
                  <span className="eval-status-val">Original training dataset referenced by checkpoint</span>
                </div>
                <div className="eval-status-item">
                  <span className="eval-status-key">Repository copy</span>
                  <span className="eval-status-val status-unavailable">Not available</span>
                </div>
                <div className="eval-status-item">
                  <span className="eval-status-key">Independent test set</span>
                  <span className="eval-status-val status-unavailable">Not available</span>
                </div>
                <div className="eval-status-item">
                  <span className="eval-status-key">Per-class ground truth</span>
                  <span className="eval-status-val status-unavailable">Not available</span>
                </div>
              </div>
            </section>
          </>
        ) : null}
      </div>
    </DashboardLayout>
  );
}
