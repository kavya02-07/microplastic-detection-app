import { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import DashboardLayout from '../components/DashboardLayout';
import StatCard from '../components/StatCard';
import ModelStatus from '../components/ModelStatus';
import RecentActivity from '../components/RecentActivity';
import { analysesAPI } from '../services/api';

export default function Dashboard() {
  const { user } = useAuth();
  const [analyses, setAnalyses] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    let isMounted = true;
    async function loadDashboardData() {
      try {
        setLoading(true);
        const data = await analysesAPI.list();
        if (isMounted) {
          setAnalyses(data || []);
        }
      } catch (err) {
        console.error('Failed to load dashboard metrics:', err);
        if (isMounted) {
          setError(err.message || 'Failed to load user analyses');
        }
      } finally {
        if (isMounted) {
          setLoading(false);
        }
      }
    }

    loadDashboardData();
    return () => {
      isMounted = false;
    };
  }, []);

  // 1. Total Analyses for authenticated user
  const totalAnalyses = analyses.length;

  // 2. Total Particles Detected across user's analyses
  const totalParticles = analyses.reduce(
    (sum, a) => sum + (typeof a.total_detections === 'number' ? a.total_detections : 0),
    0
  );

  // 3. Average Confidence (weighted mean across particles, or arithmetic mean of analyses)
  let avgConfidenceFormatted = '—';
  if (totalParticles > 0) {
    const totalWeightedScore = analyses.reduce(
      (sum, a) => sum + ((a.average_confidence || 0) * (a.total_detections || 0)),
      0
    );
    const avgScore = totalWeightedScore / totalParticles;
    avgConfidenceFormatted = (avgScore * 100).toFixed(1) + '%';
  } else if (totalAnalyses > 0) {
    const validConfAnalyses = analyses.filter((a) => typeof a.average_confidence === 'number');
    if (validConfAnalyses.length > 0) {
      const meanScore =
        validConfAnalyses.reduce((sum, a) => sum + a.average_confidence, 0) /
        validConfAnalyses.length;
      avgConfidenceFormatted = (meanScore * 100).toFixed(1) + '%';
    }
  }

  // 4. Recent Analysis
  const latestAnalysis = analyses.length > 0 ? analyses[0] : null;
  const lastAnalysisValue = latestAnalysis
    ? `#${latestAnalysis.id}`
    : 'None';
  const lastAnalysisSubtitle = latestAnalysis
    ? `${latestAnalysis.total_detections} particles • ${latestAnalysis.original_filename}`
    : 'No aquatic samples analyzed yet';

  return (
    <DashboardLayout activeTab="overview">
      <div className="dashboard-content-flow">
        {/* Welcome Section */}
        <section className="welcome-section">
          <div className="welcome-text">
            <h2>
              Welcome back, <span className="researcher-highlight">{user?.email || 'Researcher'}</span>
            </h2>
            <p>
              AI-Powered Intelligent System for Microplastic Detection, Classification and Quantitative Analysis in Aquatic Samples.
            </p>
          </div>
          <div className="session-card">
            <span className="session-label">Session ID:</span>
            <span className="session-val">{user?.id ? `USER-${user.id}` : 'ACTIVE'}</span>
          </div>
        </section>

        {/* Error notification if API failed */}
        {error && (
          <div className="alert alert-error" style={{ marginBottom: '1.5rem' }}>
            <span>⚠️ Could not refresh dashboard data: {error}</span>
          </div>
        )}

        {/* Summary Metrics Grid with REAL data */}
        <section className="stats-grid">
          <StatCard
            title="Total Analyses"
            value={loading ? '...' : totalAnalyses.toString()}
            subtitle="Samples processed across all runs"
            icon="🧪"
            isPlaceholder={false}
          />
          <StatCard
            title="Total Particles"
            value={loading ? '...' : totalParticles.toLocaleString()}
            subtitle="Identified microplastic instances"
            icon="🔬"
            isPlaceholder={false}
          />
          <StatCard
            title="Average Confidence"
            value={loading ? '...' : avgConfidenceFormatted}
            subtitle="Mean detection probability score"
            icon="📊"
            isPlaceholder={false}
          />
          <StatCard
            title="Last Analysis"
            value={loading ? '...' : lastAnalysisValue}
            subtitle={lastAnalysisSubtitle}
            icon="⏱️"
            isPlaceholder={false}
          />
        </section>

        {/* Model Status Section */}
        <section className="dashboard-section">
          <ModelStatus />
        </section>

        {/* Recent Activity Section */}
        <section className="dashboard-section">
          <RecentActivity analyses={analyses} loading={loading} />
        </section>
      </div>
    </DashboardLayout>
  );
}
