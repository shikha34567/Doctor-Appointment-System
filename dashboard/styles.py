def get_custom_css() -> str:
    return """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

    html, body, [class*="css"] {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }

    /* Main Container Padding */
    .block-container {
        padding-top: 2rem;
        padding-bottom: 3rem;
        max-width: 1200px;
    }

    /* Navbar / Header */
    .hospital-header {
        background: linear-gradient(135deg, #0e4f8a 0%, #0284c7 60%, #14b8a6 100%);
        color: white;
        padding: 1.6rem 2rem;
        border-radius: 14px;
        margin-bottom: 2rem;
        box-shadow: 0 10px 25px -5px rgba(14, 79, 138, 0.25);
    }
    .hospital-header h1 {
        margin: 0;
        font-size: 1.85rem;
        font-weight: 700;
        letter-spacing: -0.02em;
    }
    .hospital-header p {
        margin: 0.35rem 0 0 0;
        opacity: 0.92;
        font-size: 0.95rem;
    }

    /* KPI Cards */
    .kpi-card {
        background: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 12px;
        padding: 1.3rem;
        margin-bottom: 1rem;
        box-shadow: 0 2px 6px rgba(0, 0, 0, 0.04);
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    }
    .kpi-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 16px rgba(14, 165, 233, 0.12);
        border-color: #38bdf8;
    }
    .kpi-label {
        font-size: 0.8rem;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        color: #64748b;
        font-weight: 600;
        margin-bottom: 0.4rem;
    }
    .kpi-value {
        font-size: 1.9rem;
        font-weight: 700;
        color: #0f172a;
        line-height: 1.1;
    }
    .kpi-subtext {
        font-size: 0.82rem;
        color: #059669;
        margin-top: 0.4rem;
        font-weight: 500;
    }
    .kpi-subtext.alert {
        color: #dc2626;
    }

    /* Doctor Profile Card */
    .doctor-card {
        background: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 14px;
        padding: 1.4rem;
        margin-bottom: 1.2rem;
        box-shadow: 0 2px 8px rgba(0,0,0,0.03);
    }
    .doctor-name {
        font-size: 1.2rem;
        font-weight: 700;
        color: #0e4f8a;
    }
    .doctor-spec {
        display: inline-block;
        background: #e0f2fe;
        color: #0284c7;
        font-size: 0.78rem;
        font-weight: 600;
        padding: 0.25rem 0.65rem;
        border-radius: 9999px;
        margin-top: 0.3rem;
        margin-bottom: 0.6rem;
    }
    .doctor-meta {
        font-size: 0.86rem;
        color: #475569;
        line-height: 1.4;
    }

    /* Status Badges */
    .badge-scheduled {
        background: #e0f2fe;
        color: #0369a1;
        padding: 0.2rem 0.6rem;
        border-radius: 6px;
        font-size: 0.8rem;
        font-weight: 600;
    }
    .badge-completed {
        background: #dcfce7;
        color: #15803d;
        padding: 0.2rem 0.6rem;
        border-radius: 6px;
        font-size: 0.8rem;
        font-weight: 600;
    }
    .badge-cancelled {
        background: #fee2e2;
        color: #b91c1c;
        padding: 0.2rem 0.6rem;
        border-radius: 6px;
        font-size: 0.8rem;
        font-weight: 600;
    }

    /* Notice Banner */
    .notice-banner {
        background: #f0fdf4;
        border-left: 4px solid #14b8a6;
        padding: 0.9rem 1.2rem;
        border-radius: 6px;
        font-size: 0.88rem;
        color: #0f766e;
        margin-bottom: 1.4rem;
    }

    /* Disclaimer box */
    .disclaimer-box {
        background: #fffbeb;
        border: 1px solid #fef3c7;
        border-left: 4px solid #f59e0b;
        padding: 0.85rem 1.1rem;
        border-radius: 6px;
        font-size: 0.82rem;
        color: #92400e;
        margin-top: 1.5rem;
    }
    </style>
    """
