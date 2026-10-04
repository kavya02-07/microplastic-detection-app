import DetectionOverlay from './DetectionOverlay';

export default function DetectionResults({
  results,
  isHistorical = false,
  onBackToHistory,
  previewImageUrl = null,
}) {
  if (!results || typeof results !== 'object') return null;

  // Normalize detections/objects from either POST /detect or GET /analyses/{id}
  const objects = results.objects || results.detections || [];
  const id = results.id;
  const confidenceThreshold = results.confidence_threshold;
  const originalFilename = results.original_filename;
  const createdAt = results.created_at;

  const totalDetections =
    results.summary?.total_detections ??
    results.total_detections ??
    objects.length ??
    0;

  const inferenceTimeMs =
    results.summary?.inference_time_ms ??
    results.inference_time_ms ??
    null;

  // 1. Detection Confidence Metrics
  const confidences = objects
    .map((o) => o.confidence)
    .filter((c) => typeof c === 'number' && !isNaN(c));

  const avgConfidence =
    results.summary?.average_confidence ??
    results.average_confidence ??
    (confidences.length > 0
      ? confidences.reduce((a, b) => a + b, 0) / confidences.length
      : null);

  const highestConfidence =
    confidences.length > 0 ? Math.max(...confidences) : null;
  const lowestConfidence =
    confidences.length > 0 ? Math.min(...confidences) : null;
  const confidenceSpread =
    highestConfidence != null && lowestConfidence != null
      ? highestConfidence - lowestConfidence
      : null;

  // 2. Particle Measurements Metrics (calculated safely from objects)
  const validWidths = objects
    .map((o) => o.width)
    .filter((w) => typeof w === 'number' && !isNaN(w));
  const validHeights = objects
    .map((o) => o.height)
    .filter((h) => typeof h === 'number' && !isNaN(h));
  const validAreas = objects
    .map((o) => o.area)
    .filter((a) => typeof a === 'number' && !isNaN(a));
  const validAspectRatios = objects
    .map((o) => o.aspect_ratio)
    .filter((ar) => typeof ar === 'number' && !isNaN(ar));

  const avgWidth =
    validWidths.length > 0
      ? validWidths.reduce((a, b) => a + b, 0) / validWidths.length
      : null;
  const avgHeight =
    validHeights.length > 0
      ? validHeights.reduce((a, b) => a + b, 0) / validHeights.length
      : null;
  const avgArea =
    validAreas.length > 0
      ? validAreas.reduce((a, b) => a + b, 0) / validAreas.length
      : null;
  const avgAspectRatio =
    validAspectRatios.length > 0
      ? validAspectRatios.reduce((a, b) => a + b, 0) / validAspectRatios.length
      : null;

  // 3. Morphology Classes Definition & Count computation
  const morphologyClasses = [
    { name: 'Fibers', color: '#06b6d4', tagClass: 'tag-fibers' },
    { name: 'Films', color: '#3b82f6', tagClass: 'tag-films' },
    { name: 'Fragments', color: '#10b981', tagClass: 'tag-fragments' },
    { name: 'Pellets', color: '#f59e0b', tagClass: 'tag-pellets' },
  ];

  // Derive counts by class: use summary.counts_by_class if available, or compute from objects
  const counts = results.summary?.counts_by_class
    ? { ...results.summary.counts_by_class }
    : objects.reduce((acc, o) => {
        let name = o.class_name;
        // Normalize class names if needed
        if (name === 'Pallet' || name === 'Pellet') name = 'Pellets';
        if (name === 'Fiber') name = 'Fibers';
        if (name === 'Film') name = 'Films';
        if (name === 'Fragment') name = 'Fragments';

        if (name) {
          acc[name] = (acc[name] || 0) + 1;
        }
        return acc;
      }, {});

  const formatDate = (dateStr) => {
    if (!dateStr) return '—';
    try {
      const d = new Date(dateStr);
      return d.toLocaleString(undefined, {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit',
      });
    } catch {
      return dateStr;
    }
  };

  return (
    <div className={`detection-results-container ${isHistorical ? 'historical-mode' : ''}`}>
      {/* Historical Mode Notice Banner */}
      {isHistorical && (
        <div className="historical-banner-notice">
          <div className="historical-notice-content">
            <span className="historical-pulse-icon">📦</span>
            <div>
              <strong>Historical Analysis Record</strong>
              <p>Loaded from SQLite persistence. YOLO inference was not rerun.</p>
            </div>
          </div>
          {onBackToHistory && (
            <button
              type="button"
              className="btn-back-history"
              onClick={onBackToHistory}
            >
              ← Back to History
            </button>
          )}
        </div>
      )}

      {/* Header Banner */}
      <div className="results-header">
        <div className="results-title-group">
          <div className={`status-badge-icon ${isHistorical ? 'historical-badge-icon' : 'success-badge-icon'}`}>
            {isHistorical ? '🗄️' : '✓'}
          </div>
          <div>
            <h3>
              {isHistorical ? 'Historical Analysis Results' : 'Analysis Complete'}
            </h3>
            <p>
              {isHistorical
                ? `Archived record #${id} • Saved microplastic telemetry & morphometric analysis`
                : `${totalDetections} particle${totalDetections === 1 ? '' : 's'} identified • YOLOv8 Medium (weights/t29.pt)`}
            </p>
          </div>
        </div>

        <div className="results-meta-chips">
          {originalFilename && (
            <div className="meta-chip">
              <span>File:</span>
              <strong title={originalFilename}>{originalFilename}</strong>
            </div>
          )}
          {createdAt && (
            <div className="meta-chip">
              <span>Recorded:</span>
              <strong>{formatDate(createdAt)}</strong>
            </div>
          )}
          {confidenceThreshold != null && (
            <div className="meta-chip">
              <span>Threshold:</span>
              <strong>{(confidenceThreshold * 100).toFixed(0)}%</strong>
            </div>
          )}
          <div className="analysis-id-chip">
            <span>Database Record ID:</span>
            <strong>#{id}</strong>
          </div>
        </div>
      </div>

      {/* 0. Detected Particles Overlay (only available right after a fresh run —
          the original image is not persisted server-side, so History cannot show it) */}
      {previewImageUrl && (
        <div className="results-section">
          <div className="section-heading-row">
            <h4 className="section-title-label">Detected Particles</h4>
            <span className="section-caption-label">
              Bounding boxes drawn from actual model coordinates (x1, y1, x2, y2)
            </span>
          </div>
          <DetectionOverlay
            imageUrl={previewImageUrl}
            objects={objects}
            imageWidth={results.image_width}
            imageHeight={results.image_height}
          />
        </div>
      )}

      {/* 1. Analysis Overview Section */}
      <div className="results-section">
        <div className="section-heading-row">
          <h4 className="section-title-label">Analysis Overview</h4>
          <span className="section-caption-label">Core Detection Telemetry</span>
        </div>
        <div className="results-summary-grid">
          <div className="result-metric-card primary-metric">
            <span className="metric-label">Total Particles</span>
            <span className="metric-value">{totalDetections}</span>
            <span className="metric-sub">Identified Pollutants</span>
          </div>

          <div className="result-metric-card">
            <span className="metric-label">Average Confidence</span>
            <span className="metric-value">
              {avgConfidence != null ? (avgConfidence * 100).toFixed(1) + '%' : '—'}
            </span>
            <span className="metric-sub">Mean Detection Score</span>
          </div>

          <div className="result-metric-card">
            <span className="metric-label">Inference Time</span>
            <span className="metric-value">
              {inferenceTimeMs != null
                ? inferenceTimeMs > 1000
                  ? (inferenceTimeMs / 1000).toFixed(2) + ' s'
                  : inferenceTimeMs.toFixed(1) + ' ms'
                : '—'}
            </span>
            <span className="metric-sub">Execution Latency</span>
          </div>

          <div className="result-metric-card">
            <span className="metric-label">Confidence Threshold</span>
            <span className="metric-value">
              {confidenceThreshold != null
                ? (confidenceThreshold * 100).toFixed(0) + '%'
                : '—'}
            </span>
            <span className="metric-sub">Detection Cutoff</span>
          </div>
        </div>
      </div>

      {/* 2. Middle Row: Particle Classification & Analytics Summaries */}
      <div className="results-analytics-row">
        {/* Left: Particle Classification Bar Visualization */}
        <div className="analytics-card classification-card">
          <div className="card-inner-header">
            <h4 className="card-title">Particle Classification</h4>
            <span className="card-badge">{totalDetections} Total</span>
          </div>
          <p className="card-subtext">Morphology distribution across detected particles</p>

          <div className="classification-bars-list">
            {morphologyClasses.map((cls) => {
              const count = counts[cls.name] ?? 0;
              const percentage = totalDetections > 0 ? (count / totalDetections) * 100 : 0;
              return (
                <div key={cls.name} className="classification-bar-row">
                  <div className="bar-label-group">
                    <div className="bar-class-name">
                      <span className="bar-dot" style={{ backgroundColor: cls.color }}></span>
                      <strong>{cls.name}</strong>
                    </div>
                    <div className="bar-stats">
                      <span className="bar-count">
                        {count} {count === 1 ? 'particle' : 'particles'}
                      </span>
                      <span className="bar-percent">{percentage.toFixed(1)}%</span>
                    </div>
                  </div>
                  <div className="bar-track">
                    <div
                      className="bar-fill"
                      style={{
                        width: `${percentage}%`,
                        backgroundColor: cls.color,
                        boxShadow: count > 0 ? `0 0 10px ${cls.color}40` : 'none',
                      }}
                    ></div>
                  </div>
                </div>
              );
            })}
          </div>

          {/* Quick summary count pills */}
          <div className="classification-pills-row">
            {morphologyClasses.map((cls) => (
              <div key={cls.name} className={`count-pill ${cls.tagClass}-pill`}>
                <span className="pill-dot" style={{ backgroundColor: cls.color }}></span>
                <span className="pill-name">{cls.name}:</span>
                <strong className="pill-count">{counts[cls.name] ?? 0}</strong>
              </div>
            ))}
          </div>
        </div>

        {/* Right: Confidence & Particle Measurement Cards */}
        <div className="analytics-stacked-column">
          {/* Card A: Detection Confidence Summary */}
          <div className="analytics-card">
            <div className="card-inner-header">
              <h4 className="card-title">Confidence Analysis</h4>
              <span className="card-badge">Score Metrics</span>
            </div>
            <p className="card-subtext">Statistical certainty across identified particles</p>

            <div className="stats-metric-subgrid">
              <div className="subgrid-metric-item">
                <span className="subgrid-label">Average</span>
                <span className="subgrid-val">
                  {avgConfidence != null ? (avgConfidence * 100).toFixed(1) + '%' : '—'}
                </span>
                <span className="subgrid-hint">Mean particle score</span>
              </div>
              <div className="subgrid-metric-item">
                <span className="subgrid-label">Highest</span>
                <span className="subgrid-val highlight-val">
                  {highestConfidence != null
                    ? (highestConfidence * 100).toFixed(1) + '%'
                    : '—'}
                </span>
                <span className="subgrid-hint">Peak model certainty</span>
              </div>
              <div className="subgrid-metric-item">
                <span className="subgrid-label">Lowest</span>
                <span className="subgrid-val">
                  {lowestConfidence != null
                    ? (lowestConfidence * 100).toFixed(1) + '%'
                    : '—'}
                </span>
                <span className="subgrid-hint">Lowest scored particle</span>
              </div>
              <div className="subgrid-metric-item">
                <span className="subgrid-label">Range Spread</span>
                <span className="subgrid-val">
                  {confidenceSpread != null
                    ? (confidenceSpread * 100).toFixed(1) + '%'
                    : '—'}
                </span>
                <span className="subgrid-hint">Confidence delta (Δ)</span>
              </div>
            </div>

            {highestConfidence != null && lowestConfidence != null && (
              <div className="confidence-spread-bar-box">
                <div className="spread-label-row">
                  <span>Score Distribution Interval</span>
                  <strong>
                    {(lowestConfidence * 100).toFixed(0)}% → {(highestConfidence * 100).toFixed(0)}%
                  </strong>
                </div>
                <div className="spread-track">
                  <div
                    className="spread-fill"
                    style={{
                      left: `${lowestConfidence * 100}%`,
                      width: `${Math.max((highestConfidence - lowestConfidence) * 100, 2)}%`,
                    }}
                  ></div>
                </div>
              </div>
            )}
          </div>

          {/* Card B: Particle Measurements Summary */}
          <div className="analytics-card">
            <div className="card-inner-header">
              <h4 className="card-title">Particle Measurements</h4>
              <span className="card-badge">Geometric Averages</span>
            </div>
            <p className="card-subtext">Mean dimensional morphology of detected particles</p>

            <div className="measurements-grid">
              <div className="measurement-box">
                <span className="measure-label">Avg Width</span>
                <span className="measure-value">
                  {avgWidth != null ? avgWidth.toFixed(1) : '—'}
                  <span className="measure-unit">px</span>
                </span>
                <span className="measure-sub">Lateral span</span>
              </div>

              <div className="measurement-box">
                <span className="measure-label">Avg Height</span>
                <span className="measure-value">
                  {avgHeight != null ? avgHeight.toFixed(1) : '—'}
                  <span className="measure-unit">px</span>
                </span>
                <span className="measure-sub">Vertical span</span>
              </div>

              <div className="measurement-box">
                <span className="measure-label">Avg Area</span>
                <span className="measure-value">
                  {avgArea != null
                    ? avgArea.toLocaleString(undefined, { maximumFractionDigits: 1 })
                    : '—'}
                  <span className="measure-unit">px²</span>
                </span>
                <span className="measure-sub">2D Footprint</span>
              </div>

              <div className="measurement-box">
                <span className="measure-label">Avg Aspect Ratio</span>
                <span className="measure-value">
                  {avgAspectRatio != null ? avgAspectRatio.toFixed(2) : '—'}
                  <span className="measure-unit">W/H</span>
                </span>
                <span className="measure-sub">Elongation</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* 3. Detailed Particle Inventory Table */}
      <div className="objects-table-wrapper">
        <div className="table-header-group">
          <div>
            <h4 className="table-title">Detailed Particle Measurements</h4>
            <p className="table-subtext">
              Complete morphometric analysis for each identified microplastic particle
            </p>
          </div>
          <span className="table-count-tag">{objects.length} Particles</span>
        </div>

        {objects.length > 0 ? (
          <div className="table-responsive">
            <table className="detection-table">
              <thead>
                <tr>
                  <th>#</th>
                  <th>Class</th>
                  <th>Confidence</th>
                  <th>Width</th>
                  <th>Height</th>
                  <th>Area</th>
                  <th>Aspect Ratio</th>
                </tr>
              </thead>
              <tbody>
                {objects.map((obj, idx) => {
                  const displayClassName =
                    obj.class_name === 'Pallet' || obj.class_name === 'Pellet'
                      ? 'Pellets'
                      : obj.class_name === 'Fiber'
                      ? 'Fibers'
                      : obj.class_name === 'Film'
                      ? 'Films'
                      : obj.class_name === 'Fragment'
                      ? 'Fragments'
                      : obj.class_name;

                  return (
                    <tr key={idx}>
                      <td className="mono-col">{idx + 1}</td>
                      <td>
                        <span className={`class-badge-tag tag-${displayClassName?.toLowerCase()}`}>
                          {displayClassName}
                        </span>
                      </td>
                      <td className="mono-col highlight-mono">
                        {obj.confidence != null
                          ? (obj.confidence * 100).toFixed(1) + '%'
                          : '—'}
                      </td>
                      <td className="mono-col">
                        {obj.width != null ? `${obj.width.toFixed(1)} px` : '—'}
                      </td>
                      <td className="mono-col">
                        {obj.height != null ? `${obj.height.toFixed(1)} px` : '—'}
                      </td>
                      <td className="mono-col">
                        {obj.area != null
                          ? `${obj.area.toLocaleString(undefined, { maximumFractionDigits: 1 })} px²`
                          : '—'}
                      </td>
                      <td className="mono-col">
                        {obj.aspect_ratio != null ? obj.aspect_ratio.toFixed(2) : '—'}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        ) : (
          <div className="empty-results-box">
            <div className="empty-icon">🔍</div>
            <div className="empty-text">
              <h5>No Microplastic Particles Detected</h5>
              <p>
                No particles met or exceeded the confidence threshold (
                {confidenceThreshold != null ? `${(confidenceThreshold * 100).toFixed(0)}%` : 'current'}
                ). Try lowering the threshold slider or uploading a higher-magnification image.
              </p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
