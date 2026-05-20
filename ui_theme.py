"""ArtFlow AI — Streamlit custom theme."""


def inject_theme():
    import streamlit as st

    st.markdown(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=DM+Sans:opsz,wght@9..40,400;9..40,500;9..40,600;9..40,700&display=swap');

        html, body, [class*="css"] {
            font-family: 'DM Sans', system-ui, sans-serif;
        }

        .block-container {
            padding-top: 1.25rem;
            max-width: 1180px;
        }

        [data-testid="stSidebar"] {
            background: linear-gradient(180deg, #1c1917 0%, #292524 100%);
        }

        [data-testid="stSidebar"] [data-testid="stMarkdown"] p,
        [data-testid="stSidebar"] label,
        [data-testid="stSidebar"] h1,
        [data-testid="stSidebar"] h2,
        [data-testid="stSidebar"] h3 {
            color: #fafaf9 !important;
        }

        .hero-banner {
            background: linear-gradient(135deg, #1c1917 0%, #57534e 40%, #a8a29e 100%);
            border-radius: 16px;
            padding: 1.75rem 2rem;
            margin-bottom: 1.5rem;
            box-shadow: 0 8px 32px rgba(28, 25, 23, 0.2);
        }

        .hero-banner h1 {
            color: #fff !important;
            font-size: 1.75rem !important;
            font-weight: 700 !important;
            margin: 0 0 0.35rem 0 !important;
        }

        .hero-banner p {
            color: #e7e5e4 !important;
            margin: 0 !important;
            font-size: 0.95rem !important;
        }

        .section-tag {
            font-size: 0.7rem;
            font-weight: 600;
            letter-spacing: 0.08em;
            text-transform: uppercase;
            color: #78716c;
            margin-bottom: 0.25rem;
        }

        .art-card {
            background: #fafaf9;
            border: 1px solid #e7e5e4;
            border-radius: 12px;
            padding: 1rem;
            margin-bottom: 0.75rem;
        }

        div[data-testid="stMetric"] {
            background: #fafaf9;
            border: 1px solid #e7e5e4;
            border-radius: 10px;
            padding: 0.65rem 0.85rem;
        }

        .stTabs [data-baseweb="tab-list"] {
            gap: 8px;
        }

        .stTabs [data-baseweb="tab"] {
            border-radius: 8px 8px 0 0;
            padding: 8px 16px;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def hero(title: str = "ArtFlow AI", subtitle: str = ""):
    import streamlit as st

    st.markdown(
        f"""
        <div class="hero-banner">
            <h1>{title}</h1>
            <p>{subtitle}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
