import React from 'react'
import { useNavigate, useLocation } from 'react-router-dom'

const PRIMARY = '#6366f1'
const INACTIVE = '#94a3b8'

function HomeIcon({ active }) {
  return (
    <svg width="22" height="22" viewBox="0 0 24 24" fill="none">
      <path
        d="M3 10.2L12 3l9 7.2v10.2a1.6 1.6 0 0 1-1.6 1.6H4.6A1.6 1.6 0 0 1 3 20.4V10.2Z"
        fill={active ? PRIMARY : 'none'}
        stroke={active ? PRIMARY : INACTIVE}
        strokeWidth="2"
        strokeLinejoin="round"
      />
      <path
        d="M9 22V12h6v10"
        stroke={active ? '#ffffff' : INACTIVE}
        strokeWidth="2"
        strokeLinecap="round"
      />
    </svg>
  )
}

function ReceiptsIcon({ active }) {
  return (
    <svg width="22" height="22" viewBox="0 0 24 24" fill="none">
      <path
        d="M6 3h12a2 2 0 0 1 2 2v14l-3-2-3 2-3-2-3 2-2-1.3V5a2 2 0 0 1 2-2Z"
        stroke={active ? PRIMARY : INACTIVE}
        strokeWidth="1.9"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
      <path
        d="M9 8h6M9 12h6M9 15h3"
        stroke={active ? PRIMARY : INACTIVE}
        strokeWidth="1.9"
        strokeLinecap="round"
      />
    </svg>
  )
}

function CameraIcon() {
  return (
    <svg width="25" height="25" viewBox="0 0 24 24" fill="none">
      <path
        d="M23 19a2 2 0 0 1-2 2H3a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h4l2-3h6l2 3h4a2 2 0 0 1 2 2z"
        stroke="#ffffff"
        strokeWidth="2"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
      <circle cx="12" cy="13" r="4" stroke="#ffffff" strokeWidth="2" />
    </svg>
  )
}

function AnalyticsIcon({ active }) {
  return (
    <svg width="22" height="22" viewBox="0 0 24 24" fill="none">
      <rect x="3.5" y="13" width="3.8" height="8" rx="1" fill={active ? PRIMARY : INACTIVE} />
      <rect x="10.1" y="8" width="3.8" height="13" rx="1" fill={active ? PRIMARY : INACTIVE} />
      <rect x="16.7" y="4" width="3.8" height="17" rx="1" fill={active ? PRIMARY : INACTIVE} />
    </svg>
  )
}

function SettingsIcon({ active }) {
  return (
    <svg width="22" height="22" viewBox="0 0 24 24" fill="none">
      <circle cx="12" cy="12" r="3" stroke={active ? PRIMARY : INACTIVE} strokeWidth="2" />
      <path
        d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1Z"
        stroke={active ? PRIMARY : INACTIVE}
        strokeWidth="1.9"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  )
}

export default function BottomNav() {
  const navigate = useNavigate()
  const { pathname } = useLocation()

  return (
    <div style={styles.navContainer}>
      <nav style={styles.navBar}>
        {/* Home */}
        <button
          style={styles.navButton}
          onClick={() => navigate('/')}
        >
          <HomeIcon active={pathname === '/'} />
          <span style={{ ...styles.navLabel, color: pathname === '/' ? PRIMARY : INACTIVE, fontWeight: pathname === '/' ? '600' : '500' }}>
            Home
          </span>
        </button>

        {/* Receipts */}
        <button
          style={styles.navButton}
          onClick={() => navigate('/receipts')}
        >
          <ReceiptsIcon active={pathname.startsWith('/receipts')} />
          <span style={{ ...styles.navLabel, color: pathname.startsWith('/receipts') ? PRIMARY : INACTIVE, fontWeight: pathname.startsWith('/receipts') ? '600' : '500' }}>
            Receipts
          </span>
        </button>

        {/* Floating Raised Camera Button */}
        <div style={styles.centerButtonWrapper}>
          <button
            style={styles.cameraCircle}
            onClick={() => navigate('/scan')}
            aria-label="Scan Receipt"
          >
            <CameraIcon />
          </button>
        </div>

        {/* Analytics */}
        <button
          style={styles.navButton}
          onClick={() => navigate('/analytics')}
        >
          <AnalyticsIcon active={pathname === '/analytics'} />
          <span style={{ ...styles.navLabel, color: pathname === '/analytics' ? PRIMARY : INACTIVE, fontWeight: pathname === '/analytics' ? '600' : '500' }}>
            Analytics
          </span>
        </button>

        {/* Settings */}
        <button
          style={styles.navButton}
          onClick={() => navigate('/settings')}
        >
          <SettingsIcon active={pathname === '/settings'} />
          <span style={{ ...styles.navLabel, color: pathname === '/settings' ? PRIMARY : INACTIVE, fontWeight: pathname === '/settings' ? '600' : '500' }}>
            Settings
          </span>
        </button>
      </nav>

      {/* iPhone Home Indicator */}
      <div style={styles.homeIndicatorWrapper}>
        <div style={styles.homeIndicator} />
      </div>
    </div>
  )
}

const styles = {
  navContainer: {
    position: 'absolute',
    bottom: 0,
    left: 0,
    right: 0,
    width: '100%',
    backgroundColor: '#ffffff',
    borderTop: '1px solid #f1f5f9',
    zIndex: 100,
    paddingBottom: 'env(safe-area-inset-bottom, 0px)',
    boxSizing: 'border-box',
  },
  navBar: {
    height: '62px',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'space-between',
    position: 'relative',
    padding: '0 6px',
    boxSizing: 'border-box',
    width: '100%',
  },
  navButton: {
    flex: 1,
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    justifyContent: 'center',
    gap: '3px',
    background: 'none',
    border: 'none',
    cursor: 'pointer',
    padding: '4px 2px',
    minWidth: '0',
    maxWidth: '68px',
  },
  navLabel: {
    fontSize: '11px',
    letterSpacing: '-0.1px',
    lineHeight: '1.2',
  },
  centerButtonWrapper: {
    position: 'relative',
    top: '-18px',
    width: '56px',
    height: '56px',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    flexShrink: 0,
  },
  cameraCircle: {
    width: '54px',
    height: '54px',
    borderRadius: '50%',
    backgroundColor: '#6366f1',
    backgroundImage: 'linear-gradient(135deg, #6366f1 0%, #4f46e5 100%)',
    border: '3.5px solid #ffffff',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    cursor: 'pointer',
    boxShadow: '0 6px 20px rgba(99, 102, 241, 0.45)',
    transition: 'transform 0.15s ease',
  },
  homeIndicatorWrapper: {
    height: '20px',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
  },
  homeIndicator: {
    width: '130px',
    height: '4px',
    backgroundColor: '#000000',
    borderRadius: '100px',
    opacity: 0.85,
  },
}
