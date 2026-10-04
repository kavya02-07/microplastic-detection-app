import { useLocation, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

export default function Sidebar({ activeTab, onTabChange }) {
  const { user, logout } = useAuth();
  const location = useLocation();
  const navigate = useNavigate();

  // Determine current active item from path or prop
  const currentTab =
    activeTab ||
    (location.pathname === '/analyze'
      ? 'analyze'
      : location.pathname.startsWith('/history')
      ? 'history'
      : location.pathname === '/reports'
      ? 'reports'
      : location.pathname === '/model-evaluation'
      ? 'model-evaluation'
      : 'overview');

  const navItems = [
    {
      id: 'overview',
      label: 'Overview',
      path: '/dashboard',
      icon: (
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
          <rect x="3" y="3" width="7" height="7"></rect>
          <rect x="14" y="3" width="7" height="7"></rect>
          <rect x="14" y="14" width="7" height="7"></rect>
          <rect x="3" y="14" width="7" height="7"></rect>
        </svg>
      ),
    },
    {
      id: 'analyze',
      label: 'Analyze Sample',
      path: '/analyze',
      icon: (
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
          <circle cx="12" cy="12" r="10"></circle>
          <line x1="12" y1="8" x2="12" y2="12"></line>
          <line x1="12" y1="16" x2="12.01" y2="16"></line>
          <circle cx="12" cy="12" r="3"></circle>
        </svg>
      ),
    },
    {
      id: 'history',
      label: 'History',
      path: '/history',
      icon: (
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
          <circle cx="12" cy="12" r="10"></circle>
          <polyline points="12 6 12 12 16 14"></polyline>
        </svg>
      ),
    },
    {
      id: 'reports',
      label: 'Reports',
      path: '/reports',
      icon: (
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
          <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>
          <polyline points="14 2 14 8 20 8"></polyline>
          <line x1="16" y1="13" x2="8" y2="13"></line>
          <line x1="16" y1="17" x2="8" y2="17"></line>
          <polyline points="10 9 9 9 8 9"></polyline>
        </svg>
      ),
    },
    {
      id: 'model-evaluation',
      label: 'Model Evaluation',
      path: '/model-evaluation',
      icon: (
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
          <path d="M3 3v18h18"></path>
          <path d="M18.7 8 12 14.7l-3.5-3.5L3 16.7"></path>
        </svg>
      ),
    },
  ];

  const handleNavClick = (item) => {
    if (onTabChange) {
      onTabChange(item.id);
    }
    if (item.path) {
      navigate(item.path);
    }
  };

  return (
    <aside className="app-sidebar">
      {/* Branding */}
      <div className="sidebar-brand">
        <div className="brand-icon">🔬</div>
        <div className="brand-text">
          <h2>Clarium</h2>
          <span>Research Platform</span>
        </div>
      </div>

      {/* Navigation */}
      <nav className="sidebar-nav">
        <div className="nav-section-title">Navigation</div>
        <ul>
          {navItems.map((item) => (
            <li key={item.id}>
              <button
                type="button"
                className={`nav-link ${currentTab === item.id ? 'active' : ''}`}
                onClick={() => handleNavClick(item)}
              >
                <span className="nav-icon">{item.icon}</span>
                <span className="nav-label">{item.label}</span>
                {item.badge && <span className="nav-badge">{item.badge}</span>}
              </button>
            </li>
          ))}
        </ul>
      </nav>

      {/* Footer Profile & Logout */}
      <div className="sidebar-footer">
        <div className="user-profile-badge">
          <div className="user-avatar">
            {user?.email ? user.email.charAt(0).toUpperCase() : 'U'}
          </div>
          <div className="user-meta">
            <span className="user-role-label">Active Researcher</span>
            <span className="user-email-display" title={user?.email}>
              {user?.email || 'Signed in'}
            </span>
          </div>
        </div>

        <button
          type="button"
          onClick={logout}
          className="sidebar-logout-btn"
          title="Sign out of system"
        >
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"></path>
            <polyline points="16 17 21 12 16 7"></polyline>
            <line x1="21" y1="12" x2="9" y2="12"></line>
          </svg>
          <span>Logout</span>
        </button>
      </div>
    </aside>
  );
}
