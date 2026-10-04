import { useState, useRef, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import DashboardLayout from '../components/DashboardLayout';
import ImageUploader from '../components/ImageUploader';
import UploadPreview from '../components/UploadPreview';
import DetectionResults from '../components/DetectionResults';
import { detectionAPI, reportsAPI } from '../services/api';

export default function AnalyzeSample() {
  const navigate = useNavigate();
  const [selectedFile, setSelectedFile] = useState(null);
  const [errorMessage, setErrorMessage] = useState(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [confidence, setConfidence] = useState(0.25);
  const [detectionResults, setDetectionResults] = useState(null);
  const [previewUrl, setPreviewUrl] = useState(null);
  const [isDownloadingReport, setIsDownloadingReport] = useState(false);
  const hiddenChangeInputRef = useRef(null);

  // Keep an object URL of the analyzed file around so the results panel can
  // draw the model's bounding boxes over the actual uploaded image.
  useEffect(() => {
    if (!selectedFile) {
      setPreviewUrl(null);
      return undefined;
    }
    const url = URL.createObjectURL(selectedFile);
    setPreviewUrl(url);
    return () => URL.revokeObjectURL(url);
  }, [selectedFile]);

  const handleImageSelected = (file) => {
    setSelectedFile(file);
    setDetectionResults(null);
    setErrorMessage(null);
  };

  const handleRemoveImage = () => {
    setSelectedFile(null);
    setDetectionResults(null);
    setErrorMessage(null);
  };

  const handleChangeImageClick = () => {
    if (hiddenChangeInputRef.current) {
      hiddenChangeInputRef.current.value = '';
      hiddenChangeInputRef.current.click();
    }
  };

  const handleHiddenFileInput = (e) => {
    if (e.target.files && e.target.files.length > 0) {
      const file = e.target.files[0];
      const ALLOWED_TYPES = ['image/jpeg', 'image/png', 'image/webp'];
      const fileExtension = '.' + file.name.split('.').pop().toLowerCase();
      const ALLOWED_EXTENSIONS = ['.jpg', '.jpeg', '.png', '.webp'];

      if (!ALLOWED_TYPES.includes(file.type) && !ALLOWED_EXTENSIONS.includes(fileExtension)) {
        setErrorMessage(
          `Unsupported file format (${fileExtension || 'unknown'}). Please upload a JPG, PNG, or WEBP image.`
        );
        return;
      }

      if (file.size > 15 * 1024 * 1024) {
        setErrorMessage('File size exceeds the 15 MB maximum limit.');
        return;
      }

      setDetectionResults(null);
      setErrorMessage(null);
      setSelectedFile(file);
    }
  };

  const handleAnalyze = async (conf) => {
    const targetConfidence = typeof conf === 'number' ? conf : confidence;
    if (!selectedFile || isAnalyzing) return;

    setIsAnalyzing(true);
    setErrorMessage(null);

    try {
      const results = await detectionAPI.detect(selectedFile, targetConfidence);
      setDetectionResults(results);
    } catch (err) {
      console.error('Detection analysis failed:', err);
      let message = err.message;
      if (err.status === 401 || err.status === 403) {
        message = 'Authentication required. Please log in to run AI analysis.';
      } else if (!message || message.includes('Failed to fetch')) {
        message = 'Unable to connect to detection backend. Please ensure the backend server is running.';
      }
      setErrorMessage(message);
    } finally {
      setIsAnalyzing(false);
    }
  };

  const handleAnalyzeAnother = () => {
    setSelectedFile(null);
    setDetectionResults(null);
    setErrorMessage(null);
    if (hiddenChangeInputRef.current) {
      hiddenChangeInputRef.current.value = '';
    }
  };

  const handleViewFullAnalysis = () => {
    if (detectionResults?.id != null) {
      navigate(`/history/${detectionResults.id}`);
    } else {
      navigate('/history');
    }
  };

  const handleGenerateReport = async () => {
    if (!detectionResults?.id || isDownloadingReport) return;
    setIsDownloadingReport(true);
    setErrorMessage(null);
    try {
      const blob = await reportsAPI.downloadReport(detectionResults.id);
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `microplastic_report_${detectionResults.id}.pdf`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    } catch (err) {
      console.error('Report generation failed:', err);
      let message = err.message;
      if (err.status === 401 || err.status === 403) {
        message = 'Authentication required. Please log in to generate the PDF report.';
      } else if (!message || message.includes('Failed to fetch')) {
        message = 'Unable to connect to the report service. Please ensure the backend server is running.';
      }
      setErrorMessage(message || 'Failed to generate PDF report.');
    } finally {
      setIsDownloadingReport(false);
    }
  };

  const targetClasses = [
    {
      name: 'Fibers',
      id: 0,
      color: '#06b6d4',
      badgeClass: 'badge-fiber',
      description: 'Elongated synthetic microfilaments from textile laundering, cordage, and fishing nets.',
    },
    {
      name: 'Films',
      id: 1,
      color: '#3b82f6',
      badgeClass: 'badge-film',
      description: 'Thin, flexible 2D polymer fragments derived from plastic bags, wraps, and degraded packaging.',
    },
    {
      name: 'Fragments',
      id: 2,
      color: '#10b981',
      badgeClass: 'badge-fragment',
      description: 'Rigid, angular plastic particles resulting from the physical breakdown of larger debris.',
    },
    {
      name: 'Pellets',
      id: 3,
      color: '#f59e0b',
      badgeClass: 'badge-pellet',
      description: 'Spherical or lenticular pre-production polymer nurdles and cosmetic exfoliating microbeads.',
    },
  ];

  return (
    <DashboardLayout activeTab="analyze">
      <div className="analyze-page-container">
        {/* Hidden input for Change button */}
        <input
          ref={hiddenChangeInputRef}
          type="file"
          accept="image/jpeg,image/png,image/webp"
          onChange={handleHiddenFileInput}
          style={{ display: 'none' }}
        />

        {/* Header Banner */}
        <div className="analyze-header-banner">
          <div>
            <h2>Analyze Aquatic Sample</h2>
            <p>
              Upload optical microscope or stereomicroscope sample imagery for AI-driven microplastic particle detection.
            </p>
          </div>
          <div className="model-chip">
            <span className="chip-dot"></span>
            YOLOv8 Medium • weights/t29.pt
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

        {/* Main Workstation Layout */}
        <div className="analyze-grid-layout">
          {/* Left Column: Upload or Preview */}
          <div className="workstation-main-card">
            <div className="card-top-bar">
              <span className="section-title">Optical Sample Image</span>
              <span className="step-tag">
                {selectedFile ? 'Image Loaded' : 'Step 1: Upload Image'}
              </span>
            </div>

            <div className="uploader-wrapper">
              {!selectedFile ? (
                <ImageUploader
                  onImageSelected={handleImageSelected}
                  onError={(err) => setErrorMessage(err)}
                />
              ) : (
                <UploadPreview
                  file={selectedFile}
                  onRemove={handleRemoveImage}
                  onChange={handleChangeImageClick}
                  onAnalyze={handleAnalyze}
                  isAnalyzing={isAnalyzing}
                  confidence={confidence}
                  onConfidenceChange={setConfidence}
                />
              )}
            </div>
          </div>

          {/* Right Column: Taxonomy & Detection Guidelines */}
          <div className="workstation-side-card">
            <div className="card-top-bar">
              <span className="section-title">Detection Taxonomy</span>
              <span className="model-version-tag">4 Classes</span>
            </div>

            <p className="taxonomy-intro">
              The neural network is trained to identify and categorize particles into 4 distinct aquatic pollutant morphologies:
            </p>

            <div className="taxonomy-classes-list">
              {targetClasses.map((cls) => (
                <div key={cls.id} className="taxonomy-class-item">
                  <div className="class-item-head">
                    <span className="class-color-indicator" style={{ backgroundColor: cls.color }}></span>
                    <strong className="class-title-text">{cls.name}</strong>
                    <span className="class-code">Class {cls.id}</span>
                  </div>
                  <p className="class-desc-text">{cls.description}</p>
                </div>
              ))}
            </div>

            <div className="guidelines-box">
              <div className="guidelines-header">
                <span className="guide-icon">💡</span>
                <strong>Preparation Tips</strong>
              </div>
              <ul>
                <li>Ensure uniform lighting across the sample membrane.</li>
                <li>Avoid excessive particle agglomeration for accurate boundary separation.</li>
                <li>Supported formats: JPG, JPEG, PNG, WEBP (Max 15 MB).</li>
              </ul>
            </div>
          </div>
        </div>

        {/* Detection Results */}
        {detectionResults && (
          <div className="analyze-results-section">
            <DetectionResults results={detectionResults} previewImageUrl={previewUrl} />

            <div className="results-actions-bar">
              <button
                type="button"
                className="btn-action-secondary"
                onClick={handleViewFullAnalysis}
              >
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <path d="M3 3v18h18"></path>
                  <path d="M18.7 8 12 14.7l-3.5-3.5L3 16.7"></path>
                </svg>
                View Full Analysis / History
              </button>

              <button
                type="button"
                className="btn-action-secondary"
                onClick={handleGenerateReport}
                disabled={isDownloadingReport}
              >
                {isDownloadingReport ? (
                  <span className="btn-loading">
                    <span className="spinner-small"></span> Generating…
                  </span>
                ) : (
                  <>
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                      <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>
                      <polyline points="14 2 14 8 20 8"></polyline>
                      <line x1="12" y1="18" x2="12" y2="12"></line>
                      <polyline points="9 15 12 18 15 15"></polyline>
                    </svg>
                    Generate PDF Report
                  </>
                )}
              </button>

              <button
                type="button"
                className="btn-action-primary"
                onClick={handleAnalyzeAnother}
              >
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <path d="M21.5 2v6h-6M21.34 15.57a10 10 0 1 1-.57-8.38l5.67-5.67"></path>
                </svg>
                Analyze Another Sample
              </button>
            </div>
          </div>
        )}
      </div>
    </DashboardLayout>
  );
}
