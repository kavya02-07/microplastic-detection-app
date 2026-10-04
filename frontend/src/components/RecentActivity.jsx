import { useNavigate } from 'react-router-dom';

export default function RecentActivity({ analyses = [], loading = false }) {
  const navigate = useNavigate();

  const formatTimestamp = (dateStr) => {
    if (!dateStr) return '—';
    try {
      const d = new Date(dateStr);
      return d.toLocaleString(undefined, {
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
    <div className="recent-activity-card">
      <div className="activity-header">
        <div>
          <h3>Recent Activity</h3>
          <p>Historical audit log of processed aquatic sample inferences</p>
        </div>
        <div className="activity-header-actions">
          <span className="sync-badge">SQLite Storage</span>
          {analyses.length > 0 && (
            <button
              type="button"
              className="btn-view-all-link"
              onClick={() => navigate('/history')}
            >
              View Full History →
            </button>
          )}
        </div>
      </div>

      {loading ? (
        <div className="activity-loading-row">
          <span className="spinner-small"></span>
          <span>Loading activity log...</span>
        </div>
      ) : analyses.length === 0 ? (
        <div className="empty-state-box">
          <div className="empty-state-icon">📋</div>
          <h4>No Analyses Yet</h4>
          <p>
            You have not analyzed any aquatic imagery in this account yet.
            When sample detection is performed, your processed samples, classified particle counts, and confidence metrics will be logged here.
          </p>
          <button
            type="button"
            className="btn-primary"
            style={{ maxWidth: '200px', marginTop: '1rem', fontSize: '0.85rem', padding: '0.65rem 1rem' }}
            onClick={() => navigate('/analyze')}
          >
            Analyze First Sample
          </button>
        </div>
      ) : (
        <div className="recent-activity-table-wrapper">
          <table className="recent-activity-table">
            <thead>
              <tr>
                <th>Record</th>
                <th>Sample File</th>
                <th>Particles</th>
                <th>Avg Conf</th>
                <th>Timestamp</th>
                <th style={{ textAlign: 'right' }}>Action</th>
              </tr>
            </thead>
            <tbody>
              {analyses.slice(0, 5).map((item) => (
                <tr key={item.id}>
                  <td className="mono-col">
                    <span className="record-hash">#</span>{item.id}
                  </td>
                  <td>
                    <span className="recent-file-name" title={item.original_filename}>
                      {item.original_filename}
                    </span>
                  </td>
                  <td>
                    <span className="recent-count-tag">
                      {item.total_detections} detected
                    </span>
                  </td>
                  <td className="mono-col">
                    {item.average_confidence != null
                      ? (item.average_confidence * 100).toFixed(1) + '%'
                      : '—'}
                  </td>
                  <td className="date-col">
                    {formatTimestamp(item.created_at)}
                  </td>
                  <td style={{ textAlign: 'right' }}>
                    <button
                      type="button"
                      className="btn-activity-view"
                      onClick={() => navigate(`/history/${item.id}`)}
                      title={`View analysis #${item.id}`}
                    >
                      View
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
