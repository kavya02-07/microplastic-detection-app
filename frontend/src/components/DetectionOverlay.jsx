import { useState, useRef, useEffect, useCallback } from 'react';

// Same class → color mapping used elsewhere in the app (AnalyzeSample taxonomy,
// DetectionResults classification bars) so the overlay matches the rest of the UI.
const CLASS_COLORS = {
  Fibers: '#06b6d4',
  Films: '#3b82f6',
  Fragments: '#10b981',
  Pellets: '#f59e0b',
};

function normalizeClassName(name) {
  if (name === 'Pallet' || name === 'Pellet') return 'Pellets';
  if (name === 'Fiber') return 'Fibers';
  if (name === 'Film') return 'Films';
  if (name === 'Fragment') return 'Fragments';
  return name || 'Unknown';
}

/**
 * Renders `imageUrl` with the model's bounding boxes drawn on top, using the
 * actual x1/y1/x2/y2 coordinates returned by the backend (never fabricated).
 * Boxes are computed as a fraction of the true image size (imageWidth/imageHeight,
 * falling back to the loaded <img>'s natural size), then scaled against the
 * image's *rendered* size via ResizeObserver — so they track window/card resizes
 * and the image's real aspect ratio is preserved (no CSS cropping/stretching).
 */
export default function DetectionOverlay({ imageUrl, objects = [], imageWidth, imageHeight }) {
  const [renderedSize, setRenderedSize] = useState(null);
  const [naturalSize, setNaturalSize] = useState(null);
  const [loadFailed, setLoadFailed] = useState(false);
  const imgRef = useRef(null);

  useEffect(() => {
    setLoadFailed(false);
    setRenderedSize(null);
  }, [imageUrl]);

  const handleImgLoad = useCallback((e) => {
    const img = e.target;
    setRenderedSize({ width: img.clientWidth, height: img.clientHeight });
    setNaturalSize({ width: img.naturalWidth, height: img.naturalHeight });
  }, []);

  const handleImgError = useCallback(() => {
    setLoadFailed(true);
  }, []);

  useEffect(() => {
    const el = imgRef.current;
    if (!el || typeof ResizeObserver === 'undefined') return undefined;
    const observer = new ResizeObserver((entries) => {
      for (const entry of entries) {
        const { width, height } = entry.contentRect;
        if (width > 0 && height > 0) {
          setRenderedSize({ width, height });
        }
      }
    });
    observer.observe(el);
    return () => observer.disconnect();
  }, [imageUrl]);

  if (!imageUrl) return null;

  const naturalW = imageWidth || naturalSize?.width;
  const naturalH = imageHeight || naturalSize?.height;

  // Only draw boxes with real, finite coordinates — never invent positions
  // for malformed/missing detection data.
  const validBoxes = (Array.isArray(objects) ? objects : []).filter((o) => {
    const b = o?.bbox || o;
    return (
      b &&
      [b.x1, b.y1, b.x2, b.y2].every((v) => typeof v === 'number' && Number.isFinite(v))
    );
  });

  const scaleX = renderedSize && naturalW ? renderedSize.width / naturalW : null;
  const scaleY = renderedSize && naturalH ? renderedSize.height / naturalH : null;
  const canDrawBoxes = !loadFailed && scaleX && scaleY;

  return (
    <div className="detection-overlay-frame">
      {loadFailed ? (
        <div className="overlay-fallback-box">
          <span>⚠ Preview image unavailable</span>
          <p>Detection results below are unaffected.</p>
        </div>
      ) : (
        <>
          <img
            ref={imgRef}
            src={imageUrl}
            alt="Analyzed sample with detected particle bounding boxes"
            className="detection-overlay-image"
            onLoad={handleImgLoad}
            onError={handleImgError}
          />
          {canDrawBoxes && (
            <svg
              className="detection-overlay-svg"
              width={renderedSize.width}
              height={renderedSize.height}
              viewBox={`0 0 ${renderedSize.width} ${renderedSize.height}`}
              preserveAspectRatio="none"
            >
              {validBoxes.map((o, idx) => {
                const b = o.bbox || o;
                const displayClass = normalizeClassName(o.class_name);
                const color = CLASS_COLORS[displayClass] || '#94a3b8';
                const x = Math.min(b.x1, b.x2) * scaleX;
                const y = Math.min(b.y1, b.y2) * scaleY;
                const w = Math.max(Math.abs(b.x2 - b.x1) * scaleX, 2);
                const h = Math.max(Math.abs(b.y2 - b.y1) * scaleY, 2);
                const confPct = typeof o.confidence === 'number' ? `${(o.confidence * 100).toFixed(0)}%` : '';
                const labelText = confPct ? `${displayClass} ${confPct}` : displayClass;
                const labelWidth = Math.min(Math.max(labelText.length * 6 + 12, 42), renderedSize.width);
                const labelAbove = y >= 16;
                const labelY = labelAbove ? y - 16 : Math.min(y + h + 1, renderedSize.height - 15);

                return (
                  <g key={o.id ?? idx} className="det-box-group">
                    <rect
                      x={x}
                      y={y}
                      width={w}
                      height={h}
                      fill="none"
                      stroke={color}
                      strokeWidth="2"
                      rx="2"
                    />
                    <rect x={x} y={labelY} width={labelWidth} height="15" rx="2" fill={color} />
                    <text x={x + 5} y={labelY + 11} fontSize="10" fontWeight="700" fill="#0a0e17">
                      {labelText}
                    </text>
                  </g>
                );
              })}
            </svg>
          )}
        </>
      )}
    </div>
  );
}
