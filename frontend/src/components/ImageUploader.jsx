import { useState, useRef } from 'react';

const ALLOWED_TYPES = ['image/jpeg', 'image/png', 'image/webp'];
const ALLOWED_EXTENSIONS = ['.jpg', '.jpeg', '.png', '.webp'];
const MAX_FILE_SIZE_BYTES = 15 * 1024 * 1024; // 15 MB

export default function ImageUploader({ onImageSelected, onError }) {
  const [isDragging, setIsDragging] = useState(false);
  const fileInputRef = useRef(null);

  const validateAndProcessFile = (file) => {
    if (!file) return;

    // 1. Validate file type
    const fileExtension = '.' + file.name.split('.').pop().toLowerCase();
    const isMimeValid = ALLOWED_TYPES.includes(file.type);
    const isExtValid = ALLOWED_EXTENSIONS.includes(fileExtension);

    if (!isMimeValid && !isExtValid) {
      onError?.(
        `Unsupported file format (${fileExtension || 'unknown'}). Please upload a JPG, PNG, or WEBP image.`
      );
      return;
    }

    // 2. Validate file size
    if (file.size > MAX_FILE_SIZE_BYTES) {
      const sizeMB = (file.size / (1024 * 1024)).toFixed(1);
      onError?.(
        `File size (${sizeMB} MB) exceeds the 15 MB maximum limit. Please select a smaller sample image.`
      );
      return;
    }

    // Valid file
    onError?.(null);
    onImageSelected(file);
  };

  const handleDragOver = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(true);
  };

  const handleDragLeave = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);

    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      validateAndProcessFile(e.dataTransfer.files[0]);
    }
  };

  const handleFileInputChange = (e) => {
    if (e.target.files && e.target.files.length > 0) {
      validateAndProcessFile(e.target.files[0]);
    }
  };

  const triggerFileInput = () => {
    if (fileInputRef.current) {
      fileInputRef.current.value = ''; // Reset input so same file can be re-selected if needed
      fileInputRef.current.click();
    }
  };

  return (
    <div
      className={`upload-dropzone ${isDragging ? 'drag-over' : ''}`}
      onDragOver={handleDragOver}
      onDragEnter={handleDragOver}
      onDragLeave={handleDragLeave}
      onDrop={handleDrop}
      onClick={triggerFileInput}
      role="button"
      tabIndex={0}
      onKeyDown={(e) => {
        if (e.key === 'Enter' || e.key === ' ') {
          e.preventDefault();
          triggerFileInput();
        }
      }}
    >
      <input
        ref={fileInputRef}
        type="file"
        accept="image/jpeg,image/png,image/webp"
        onChange={handleFileInputChange}
        style={{ display: 'none' }}
      />

      <div className="dropzone-content">
        <div className="dropzone-icon">
          <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75">
            <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>
            <polyline points="17 8 12 3 7 8"></polyline>
            <line x1="12" y1="3" x2="12" y2="15"></line>
          </svg>
        </div>

        <div className="dropzone-text">
          <h3>Drag and drop aquatic sample image here</h3>
          <p>Support for microscopic and high-resolution petri-dish photographs</p>
        </div>

        <div className="dropzone-divider">
          <span>or</span>
        </div>

        <button
          type="button"
          className="btn-choose-file"
          onClick={(e) => {
            e.stopPropagation();
            triggerFileInput();
          }}
        >
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <rect x="3" y="3" width="18" height="18" rx="2" ry="2"></rect>
            <circle cx="8.5" cy="8.5" r="1.5"></circle>
            <polyline points="21 15 16 10 5 21"></polyline>
          </svg>
          Choose Image File
        </button>

        <div className="dropzone-formats">
          <span>Accepted Formats: <strong>JPG, JPEG, PNG, WEBP</strong></span>
          <span className="dot-sep">•</span>
          <span>Max File Size: <strong>15 MB</strong></span>
        </div>
      </div>
    </div>
  );
}
