import React from 'react'

const DEFAULT_BUDGET = 20000

function formatINR(val) {
  if (val === null || val === undefined) return '₹ 0'
  return '₹ ' + Math.round(val).toLocaleString('en-IN')
}

export default function TotalExpensesCard({ total = 12450, budget = DEFAULT_BUDGET, loading = false }) {
  const effectiveTotal = total || 0
  const effectiveBudget = budget || DEFAULT_BUDGET
  const pct = Math.min(100, Math.max(0, Math.round((effectiveTotal / effectiveBudget) * 100)))
  const remaining = Math.max(0, effectiveBudget - effectiveTotal)

  if (loading) {
    return (
      <div style={styles.card}>
        <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '14px' }}>
          <div>
            <div className="skeleton" style={{ width: '90px', height: '12px', marginBottom: '8px' }} />
            <div className="skeleton" style={{ width: '130px', height: '30px' }} />
          </div>
          <div className="skeleton" style={{ width: '90px', height: '18px' }} />
        </div>
        <div className="skeleton" style={{ width: '100%', height: '8px', borderRadius: '9999px', marginBottom: '10px' }} />
        <div style={{ display: 'flex', justifyContent: 'space-between' }}>
          <div className="skeleton" style={{ width: '120px', height: '12px' }} />
          <div className="skeleton" style={{ width: '60px', height: '12px' }} />
        </div>
      </div>
    )
  }

  return (
    <div style={styles.card}>
      {/* Top Header Row */}
      <div style={styles.topRow}>
        <div style={styles.amountBlock}>
          <span style={styles.label}>TOTAL EXPENSES</span>
          <div style={styles.amount}>{formatINR(effectiveTotal)}</div>
        </div>

        <div style={styles.budgetBlock}>
          <span style={styles.budgetPrefix}>Budget: </span>
          <span style={styles.budgetVal}>₹{Math.round(effectiveBudget).toLocaleString('en-IN')}</span>
        </div>
      </div>

      {/* Gradient Progress Bar */}
      <div style={styles.progressTrack}>
        <div
          style={{
            ...styles.progressFill,
            width: `${pct}%`,
          }}
        />
      </div>

      {/* Bottom Summary Row */}
      <div style={styles.bottomRow}>
        <span style={styles.percentText}>{pct}% of monthly budget used</span>
        <span style={styles.remainingText}>₹{Math.round(remaining).toLocaleString('en-IN')} left</span>
      </div>
    </div>
  )
}

const styles = {
  card: {
    backgroundColor: '#ffffff',
    borderRadius: '20px',
    padding: '18px 16px',
    marginBottom: '14px',
    boxShadow: '0 2px 10px rgba(0, 0, 0, 0.02)',
    boxSizing: 'border-box',
    width: '100%',
  },
  topRow: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
    marginBottom: '14px',
  },
  amountBlock: {
    display: 'flex',
    flexDirection: 'column',
    gap: '3px',
  },
  label: {
    fontSize: '11.5px',
    fontWeight: '600',
    color: '#64748b',
    letterSpacing: '0.06em',
  },
  amount: {
    fontSize: '28px',
    fontWeight: '800',
    color: '#0f172a',
    letterSpacing: '-0.7px',
    lineHeight: '1.1',
  },
  budgetBlock: {
    paddingTop: '16px',
    display: 'flex',
    alignItems: 'baseline',
    gap: '2px',
  },
  budgetPrefix: {
    fontSize: '13px',
    fontWeight: '500',
    color: '#64748b',
  },
  budgetVal: {
    fontSize: '14px',
    fontWeight: '700',
    color: '#0f172a',
  },
  progressTrack: {
    height: '8px',
    backgroundColor: '#f1f5f9',
    borderRadius: '9999px',
    overflow: 'hidden',
    marginBottom: '10px',
  },
  progressFill: {
    height: '100%',
    borderRadius: '9999px',
    backgroundImage: 'linear-gradient(90deg, #6366f1 0%, #06b6d4 100%)',
    transition: 'width 0.5s cubic-bezier(0.4, 0, 0.2, 1)',
  },
  bottomRow: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  percentText: {
    fontSize: '12px',
    fontWeight: '500',
    color: '#64748b',
  },
  remainingText: {
    fontSize: '12.5px',
    fontWeight: '700',
    color: '#6366f1',
  },
}
