import React, { useState } from 'react'

const BUDGET_KEY = 'khatascan_budget'

export default function SettingsPage() {
  const [budget, setBudget] = useState(() => {
    const saved = localStorage.getItem(BUDGET_KEY)
    return saved ? Number(saved) : 20000
  })
  const [savedStatus, setSavedStatus] = useState(false)

  const handleSaveBudget = () => {
    localStorage.setItem(BUDGET_KEY, String(budget))
    setSavedStatus(true)
    setTimeout(() => setSavedStatus(false), 2000)
  }

  return (
    <div className="page-inner" style={{ padding: '16px 20px 24px' }}>
      {/* Header */}
      <div style={styles.header}>
        <h2 style={styles.title}>Settings</h2>
      </div>

      <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
        {/* Profile Card */}
        <div style={styles.card}>
          <div style={styles.profileRow}>
            <div style={styles.avatarWrapper}>
              <div style={styles.avatarCircle}>
                <span style={styles.avatarInitials}>PC</span>
              </div>
              <div style={styles.activeDot} />
            </div>
            <div>
              <h3 style={styles.profileName}>Praveen C.</h3>
              <p style={styles.profileRole}>Khatascan User &bull; Free Plan</p>
            </div>
          </div>
        </div>

        {/* Monthly Budget Setting */}
        <div style={styles.card}>
          <h3 style={styles.sectionHeading}>Monthly Budget</h3>
          <p style={styles.sectionSub}>Set your monthly spending ceiling for expense tracking</p>
          <div style={styles.budgetInputGroup}>
            <span style={styles.currencyPrefix}>₹</span>
            <input
              type="number"
              style={styles.budgetInput}
              value={budget}
              onChange={(e) => {
                setBudget(Number(e.target.value))
                setSavedStatus(false)
              }}
              min="0"
              step="500"
            />
          </div>
          <button
            className="btn btn-primary"
            style={{ width: '100%', justifyContent: 'center', backgroundColor: savedStatus ? '#22c55e' : '#6366f1' }}
            onClick={handleSaveBudget}
          >
            {savedStatus ? '✓ Saved!' : 'Save Budget'}
          </button>
        </div>

        {/* System & Connection Info */}
        <div style={styles.card}>
          <h3 style={styles.sectionHeading}>System Information</h3>
          <div style={styles.infoRow}>
            <span style={styles.infoKey}>Application</span>
            <span style={styles.infoValue}>Khatascan Mobile</span>
          </div>
          <div style={styles.infoRow}>
            <span style={styles.infoKey}>Version</span>
            <span style={styles.infoValue}>2.0.0</span>
          </div>
          <div style={styles.infoRow}>
            <span style={styles.infoKey}>Backend API</span>
            <span style={styles.infoValue}>{import.meta.env.VITE_API_URL || 'http://localhost:8000'}</span>
          </div>
          <div style={styles.infoRow}>
            <span style={styles.infoKey}>OCR Engine</span>
            <span style={styles.infoValue}>Google Gemini Flash / RapidOCR</span>
          </div>
        </div>
      </div>
    </div>
  )
}

const styles = {
  header: {
    marginBottom: '20px',
    paddingTop: '6px',
  },
  title: {
    fontSize: '24px',
    fontWeight: '800',
    color: '#0f172a',
    letterSpacing: '-0.5px',
  },
  card: {
    backgroundColor: '#ffffff',
    borderRadius: '24px',
    padding: '22px 20px',
    boxShadow: '0 2px 12px rgba(0, 0, 0, 0.03)',
  },
  profileRow: {
    display: 'flex',
    alignItems: 'center',
    gap: '16px',
  },
  avatarWrapper: {
    position: 'relative',
  },
  avatarCircle: {
    width: '54px',
    height: '54px',
    borderRadius: '50%',
    backgroundColor: '#0f172a',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    border: '2px solid #334155',
  },
  avatarInitials: {
    color: '#ffffff',
    fontSize: '18px',
    fontWeight: '700',
  },
  activeDot: {
    position: 'absolute',
    bottom: '0',
    right: '0',
    width: '13px',
    height: '13px',
    borderRadius: '50%',
    backgroundColor: '#22c55e',
    border: '2.5px solid #ffffff',
  },
  profileName: {
    fontSize: '17px',
    fontWeight: '700',
    color: '#0f172a',
  },
  profileRole: {
    fontSize: '13px',
    color: '#94a3b8',
    marginTop: '2px',
  },
  sectionHeading: {
    fontSize: '16px',
    fontWeight: '700',
    color: '#0f172a',
    marginBottom: '4px',
  },
  sectionSub: {
    fontSize: '13px',
    color: '#64748b',
    marginBottom: '16px',
  },
  budgetInputGroup: {
    display: 'flex',
    alignItems: 'center',
    border: '1.5px solid #e2e8f0',
    borderRadius: '14px',
    overflow: 'hidden',
    marginBottom: '14px',
    backgroundColor: '#f8fafc',
  },
  currencyPrefix: {
    padding: '12px 16px',
    fontSize: '18px',
    fontWeight: '700',
    color: '#6366f1',
    backgroundColor: '#eef2ff',
    borderRight: '1.5px solid #e2e8f0',
  },
  budgetInput: {
    flex: 1,
    padding: '12px 14px',
    fontSize: '18px',
    fontWeight: '700',
    color: '#0f172a',
    border: 'none',
    outline: 'none',
    backgroundColor: 'transparent',
    fontFamily: 'inherit',
  },
  infoRow: {
    display: 'flex',
    justifyContent: 'space-between',
    padding: '11px 0',
    borderBottom: '1px solid #f1f5f9',
    fontSize: '13.5px',
  },
  infoKey: {
    color: '#64748b',
  },
  infoValue: {
    fontWeight: '600',
    color: '#0f172a',
    maxWidth: '60%',
    textAlign: 'right',
    wordBreak: 'break-all',
  },
}
