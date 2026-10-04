import { useAuth } from '../context/AuthContext';

export default function Navbar() {
  const { user, logout } = useAuth();

  return (
    <header className="app-header">
      <div className="header-brand">
        <div className="brand-logo">🔬</div>
        <div className="brand-title">
          <h1>Clarium</h1>
          <span>Microplastic Detection & Quantification System</span>
        </div>
      </div>

      {user && (
        <div className="header-user-menu">
          <div className="user-badge">
            <span className="status-dot"></span>
            <span className="user-email">{user.email}</span>
          </div>
          <button onClick={logout} className="btn-logout" title="Sign out">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"></path>
              <polyline points="16 17 21 12 16 7"></polyline>
              <line x1="21" y1="12" x2="9" y2="12"></line>
            </svg>
            Sign Out
          </button>
        </div>
      )}
    </header>
  );
}
