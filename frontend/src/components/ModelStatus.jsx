export default function ModelStatus() {
  const classes = [
    { id: 0, name: 'Fibers', color: '#06b6d4', desc: 'Elongated synthetic filaments' },
    { id: 1, name: 'Films', color: '#3b82f6', desc: 'Flat flexible sheet polymers' },
    { id: 2, name: 'Fragments', color: '#10b981', desc: 'Irregular angular breakdown pieces' },
    { id: 3, name: 'Pellets', color: '#f59e0b', desc: 'Spherical polymer nurdles' },
  ];

  return (
    <div className="model-status-card">
      <div className="model-header">
        <div className="model-title-group">
          <div className="model-icon-badge">🧠</div>
          <div>
            <h3>Inference Model Architecture</h3>
            <p>Active Deep Learning Detector for Microplastic Identification</p>
          </div>
        </div>
        <div className="model-online-pill">
          <span className="pulse-dot"></span>
          <span>Online & Ready</span>
        </div>
      </div>

      <div className="model-specs-grid">
        <div className="spec-item">
          <span className="spec-label">Model Engine</span>
          <span className="spec-value">YOLOv8 Medium</span>
        </div>
        <div className="spec-item">
          <span className="spec-label">Model Weights File</span>
          <span className="spec-value spec-mono">weights/t29.pt</span>
        </div>
        <div className="spec-item">
          <span className="spec-label">Inference Target</span>
          <span className="spec-value">Object Detection (xyxy)</span>
        </div>
        <div className="spec-item">
          <span className="spec-label">Pre-loaded Memory</span>
          <span className="spec-value">Singleton Cached in Backend</span>
        </div>
      </div>

      <div className="taxonomy-section">
        <h4 className="taxonomy-title">Detected Classes (4 Trained Types):</h4>
        <div className="classes-grid">
          {classes.map((cls) => (
            <div key={cls.id} className="class-card">
              <div className="class-card-header">
                <span className="class-dot" style={{ backgroundColor: cls.color }}></span>
                <span className="class-name">{cls.name}</span>
                <span className="class-id-badge">ID {cls.id}</span>
              </div>
              <p className="class-desc">{cls.desc}</p>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
