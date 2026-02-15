import streamlit as st


def inject_css():
    st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

    /* ── Global ── */
    html, body, [class*="css"] { font-family: 'Inter', sans-serif !important; }
    div[data-testid="stSidebar"] {
        background: rgba(10, 10, 20, 0.95);
        backdrop-filter: blur(20px);
    }
    .block-container { padding: 1rem 1.5rem 3rem; max-width: 100%; }

    /* ── Headings ── */
    h1 {
        background: linear-gradient(135deg, #a78bfa, #818cf8, #06b6d4);
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
        font-weight: 800 !important; font-size: 1.7rem !important;
        letter-spacing: -0.02em;
    }
    h2, h3, h4 { color: #e2e8f0 !important; letter-spacing: -0.01em; }

    /* ── Glass Cards ── */
    .glass {
        background: rgba(15, 15, 26, 0.6);
        backdrop-filter: blur(16px); -webkit-backdrop-filter: blur(16px);
        border: 1px solid rgba(167, 139, 250, 0.1);
        border-radius: 16px; padding: 1rem 1.2rem;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    }
    .glass:hover {
        border-color: rgba(167, 139, 250, 0.25);
        box-shadow: 0 4px 24px rgba(129, 140, 248, 0.08);
    }

    /* ── KPI Grid ── */
    .kpi-grid {
        display: grid; grid-template-columns: repeat(4, 1fr);
        gap: 0.75rem; margin-bottom: 1rem;
    }
    .kpi {
        background: rgba(15, 15, 26, 0.6);
        backdrop-filter: blur(16px); -webkit-backdrop-filter: blur(16px);
        border: 1px solid rgba(167, 139, 250, 0.1);
        border-radius: 16px; padding: 1rem;
        text-align: center;
        transition: all 0.3s ease;
    }
    .kpi:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 24px rgba(129, 140, 248, 0.12);
    }
    .kpi-label { color: #94a3b8; font-size: 0.72rem; text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 4px; }
    .kpi-val { font-size: 1.35rem; font-weight: 700; }
    .green { color: #34d399; } .red { color: #f87171; } .white { color: #e2e8f0; } .blue { color: #818cf8; }

    /* ── Category Bars ── */
    .cat-row {
        background: rgba(15, 15, 26, 0.5);
        border-radius: 12px; padding: 0.6rem 0.9rem;
        margin-bottom: 0.35rem;
        border: 1px solid rgba(255,255,255,0.03);
        transition: all 0.2s ease;
    }
    .cat-row:hover { background: rgba(15, 15, 26, 0.8); }
    .cat-header { display: flex; justify-content: space-between; font-size: 0.82rem; margin-bottom: 4px; }
    .cat-name { color: #e2e8f0; font-weight: 500; }
    .cat-amount { color: #a78bfa; font-weight: 600; }
    .cat-track { background: rgba(255,255,255,0.06); border-radius: 6px; height: 6px; overflow: hidden; }
    .cat-fill { height: 100%; border-radius: 6px; transition: width 0.5s ease; }

    /* ── Timeline ── */
    .day-header {
        color: #a78bfa; font-weight: 600; font-size: 0.88rem;
        padding: 0.5rem 0 0.2rem;
        border-bottom: 1px solid rgba(167, 139, 250, 0.1);
        margin-bottom: 0.2rem;
        display: flex; justify-content: space-between;
    }
    .day-total { font-weight: 400; font-size: 0.78rem; }

    .txn {
        background: rgba(15, 15, 26, 0.45);
        border: 1px solid rgba(255, 255, 255, 0.03);
        border-radius: 12px; padding: 0.55rem 0.75rem;
        margin-bottom: 0.2rem;
        transition: all 0.2s ease;
    }
    .txn:hover {
        background: rgba(15, 15, 26, 0.8);
        border-color: rgba(167, 139, 250, 0.12);
        transform: translateX(3px);
    }
    .txn-row { display: flex; align-items: center; justify-content: space-between; }
    .txn-left { display: flex; align-items: center; gap: 0.55rem; }
    .txn-icon { font-size: 1.1rem; }
    .txn-ens { color: #e2e8f0; font-weight: 500; font-size: 0.84rem; }
    .txn-cat { color: #64748b; font-size: 0.68rem; }
    .txn-amt { font-weight: 700; font-size: 0.88rem; white-space: nowrap; }
    .txn-added { color: #818cf8; font-size: 0.62rem; font-style: italic; }

    /* ── User Items ── */
    .user-card {
        background: rgba(15, 15, 26, 0.5);
        border: 1px solid rgba(255,255,255,0.05);
        border-radius: 14px; padding: 0.7rem 1rem;
        margin-bottom: 0.4rem;
        display: flex; align-items: center; justify-content: space-between;
        transition: all 0.2s ease;
    }
    .user-card:hover { background: rgba(15, 15, 26, 0.8); }
    .user-info { display: flex; align-items: center; gap: 0.6rem; }
    .user-avatar { font-size: 1.4rem; }
    .user-name { color: #e2e8f0; font-weight: 600; font-size: 0.88rem; }
    .user-handle { color: #64748b; font-size: 0.72rem; }
    .user-badge {
        display: inline-block; padding: 0.15rem 0.5rem; border-radius: 10px;
        font-size: 0.7rem; font-weight: 500;
    }
    .badge-pending { background: rgba(251, 191, 36, 0.15); color: #fbbf24; }
    .badge-friend { background: rgba(52, 211, 153, 0.15); color: #34d399; }

    /* ── Top Bar ── */
    .topbar {
        display: flex; align-items: center; justify-content: space-between;
        margin-bottom: 0.8rem;
    }
    .topbar-user {
        display: flex; align-items: center; gap: 0.5rem;
        color: #e2e8f0; font-weight: 500; font-size: 0.9rem;
    }
    .topbar-avatar { font-size: 1.5rem; }

    /* ── Responsive ── */
    @media (max-width: 768px) {
        .block-container { padding: 0.5rem 0.6rem 2rem; }
        h1 { font-size: 1.3rem !important; }
        .kpi-grid { grid-template-columns: repeat(2, 1fr); gap: 0.5rem; }
        .kpi { padding: 0.7rem 0.5rem; }
        .kpi-val { font-size: 1.05rem; }
        .kpi-label { font-size: 0.65rem; }
        [data-testid="column"] { min-width: 100% !important; }
        .txn { padding: 0.45rem 0.55rem; }
        .txn-ens { font-size: 0.8rem; }
        .txn-amt { font-size: 0.82rem; }
    }
    @media (max-width: 480px) {
        .kpi-val { font-size: 0.92rem; }
        h1 { font-size: 1.1rem !important; }
        .day-header { font-size: 0.82rem; }
    }
</style>
""", unsafe_allow_html=True)
