import { useState, useEffect } from 'react';

export default function UploadPreview({
  file,
  onRemove,
  onChange,
  onAnalyze,
  isAnalyzing = false,
  confidence = 0.25,
  onConfidenceChange,
}) {
  const [previewUrl, setPreviewUrl] = useState(null);
  const [imageDimensions, setImageDimensions] = useState(null);

  useEffect(() => {
    if (!file) {
      setPreviewUrl(null);
      setImageDimensions(null);
      return;
    }

    const objectUrl = URL.createObjectURL(file);
    setPreviewUrl(objectUrl);

    // Read dimensions
    const img = new Image();
    img.onload = () => {
      setImageDimensions({ width: img.naturalWidth, height: img.naturalHeight });
    };
    img.src = objectUrl;

    return () => {
      URL.revokeObjectURL(objectUrl);
    };
  }, [file]);

  const formatFileSize = (bytes) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  const handleAnalyzeClick = () => {
    if (onAnalyze && !isAnalyzing && file) {
      onAnalyze(confidence);
    }
  };

  if (!file) return null;

  return (
    <div className="upload-preview-container">
      <div className="preview-media-box">
        {previewUrl ? (
          <img src={previewUrl} alt={file.name} className="preview-image" />
        ) : (
          <div className="preview-placeholder">Loading image preview...</div>
        )}
      </div>

      <div className="preview-metadata-panel">
        <div className="metadata-header">
          <div className="file-info-col">
            <span className="file-name-label" title={file.name}>
              {file.name}
            </span>
            <div className="file-specs-row">
              <span className="file-spec-chip">{formatFileSize(file.size)}</span>
              <span className="file-spec-chip">{file.type || 'image/jpeg'}</span>
              {imageDimensions && (
                <span className="file-spec-chip">
                  {imageDimensions.width} × {imageDimensions.height} px
                </span>
              )}
            </div>
          </div>

          <div className="preview-actions">
            <button
              type="button"
              className="btn-action btn-change"
              onClick={onChange}
              disabled={isAnalyzing}
              title="Select a different image"
            >
              <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M21.5 2v6h-6M21.34 15.57a10 10 0 1 1-.57-8.38l5.67-5.67"></path>
              </svg>
              Change
            </button>
            <button
              type="button"
              className="btn-action btn-remove"
              onClick={onRemove}
              disabled={isAnalyzing}
              title="Remove this image"
            >
              <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <polyline points="3 6 5 6 21 6"></polyline>
                <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path>
              </svg>
              Remove
            </button>
          </div>
        </div>

        {/* Confidence Threshold Setting */}
        <div className="confidence-control-box">
          <div className="confidence-label-row">
            <label htmlFor="confidence-slider">
              Confidence Threshold: <strong>{(confidence * 100).toFixed(0)}%</strong>
            </label>
            <span className="confidence-hint">(0.05 - 1.00)</span>
          </div>
          <div className="slider-row">
            <input
              id="confidence-slider"
              type="range"
              min="0.05"
              max="0.95"
              step="0.05"
              value={confidence}
              onChange={(e) => onConfidenceChange?.(parseFloat(e.target.value))}
              disabled={isAnalyzing}
              className="confidence-slider"
            />
            <span className="confidence-val-chip">{confidence.toFixed(2)}</span>
          </div>
        </div>

        <div className="preview-footer">
          <div className="status-indicator-badge">
            <span className={isAnalyzing ? 'dot-analyzing' : 'dot-ready'}></span>
            <span>
              {isAnalyzing
                ? 'Running YOLOv8 Deep Inference...'
                : 'Sample Ready for AI Analysis'}
            </span>
          </div>

          <button
            type="button"
            className="btn-analyze-sample"
            onClick={handleAnalyzeClick}
            disabled={!file || isAnalyzing}
          >
            {isAnalyzing ? (
              <span className="btn-loading">
                <span className="spinner-small"></span> Analyzing Sample...
              </span>
            ) : (
              <>
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <polygon points="5 3 19 12 5 21 5 3"></polygon>
                </svg>
                Analyze Sample
              </>
            )}
          </button>
        </div>
      </div>
    </div>
  );
}
