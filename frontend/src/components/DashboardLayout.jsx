import Sidebar from './Sidebar';

export default function DashboardLayout({ children, activeTab = 'overview', onTabChange }) {
  return (
    <div className="dashboard-shell">
      <Sidebar activeTab={activeTab} onTabChange={onTabChange} />
      <div className="dashboard-main-wrapper">
        <header className="dashboard-topbar">
          <div className="topbar-left">
            <span className="system-status-indicator"></span>
            <span className="system-status-text">AI Core: YOLOv8 (t29.pt) Online</span>
          </div>
          <div className="topbar-right">
            <span className="environment-tag">System Ready</span>
          </div>
        </header>
        <main className="dashboard-main-content">
          {children}
        </main>
      </div>
    </div>
  );
}
