import streamlit as st

T = {
    'bg':         '#0e1216',
    'bg2':        '#151a20',
    'bg3':        '#1c232b',
    'surface':    '#171d24',
    'surfaceHi':  '#1f262e',
    'border':     '#252d36',
    'borderHi':   '#323b45',
    'text':       '#e6e8eb',
    'textDim':    '#9aa3ad',
    'textMute':   '#6b7682',
    'accent':     '#4ade80',
    'accentDim':  'rgba(74,222,128,0.12)',
    'customer':   '#34d399',
    'customerBg': 'rgba(52,211,153,0.14)',
    'lead':       '#60a5fa',
    'leadDim':    'rgba(96,165,250,0.12)',
    'signed':     '#fbbf24',
    'signedDim':  'rgba(251,191,36,0.12)',
    'webinar':    '#a78bfa',
    'webinarDim': 'rgba(167,139,250,0.14)',
    'call':       '#f472b6',
    'callDim':    'rgba(244,114,182,0.14)',
    'form':       '#22d3ee',
    'formDim':    'rgba(34,211,238,0.14)',
}

CHANNEL_META = {
    'Direct':         {'dot': '#9aa3ad', 'tint': 'rgba(154,163,173,0.12)'},
    'Organic Search': {'dot': '#34d399', 'tint': 'rgba(52,211,153,0.12)'},
    'Paid Search':    {'dot': '#fbbf24', 'tint': 'rgba(251,191,36,0.12)'},
    'Affiliates':     {'dot': '#f472b6', 'tint': 'rgba(244,114,182,0.12)'},
    'Referral':       {'dot': '#60a5fa', 'tint': 'rgba(96,165,250,0.12)'},
    'Email':          {'dot': '#22d3ee', 'tint': 'rgba(34,211,238,0.12)'},
    'Calendly':       {'dot': '#fb923c', 'tint': 'rgba(251,146,60,0.14)'},
    'WebinarGeek':    {'dot': '#a78bfa', 'tint': 'rgba(167,139,250,0.14)'},
    'Social':         {'dot': '#f87171', 'tint': 'rgba(248,113,113,0.12)'},
}

STATUS_META = {
    'customer':  {'label': 'CUSTOMER',  'color': '#34d399', 'bg': 'rgba(52,211,153,0.14)'},
    'lead':      {'label': 'LEAD',      'color': '#60a5fa', 'bg': 'rgba(96,165,250,0.12)'},
    'signed-up': {'label': 'SIGNED UP', 'color': '#fbbf24', 'bg': 'rgba(251,191,36,0.12)'},
    'churned':   {'label': 'CHURNED',   'color': '#f87171', 'bg': 'rgba(248,113,113,0.12)'},
}

ACTIVITY_META = {
    'first_session':        {'label': 'First session',        'color': '#9aa3ad', 'bg': 'rgba(154,163,173,0.12)'},
    'form_submission':      {'label': 'Form submission',      'color': '#22d3ee', 'bg': 'rgba(34,211,238,0.14)'},
    'webinar_registration': {'label': 'Webinar registration', 'color': '#a78bfa', 'bg': 'rgba(167,139,250,0.14)'},
    'calendly_booking':     {'label': 'Calendly booking',     'color': '#f472b6', 'bg': 'rgba(244,114,182,0.14)'},
    'signup':               {'label': 'Signed up',            'color': '#fbbf24', 'bg': 'rgba(251,191,36,0.12)'},
    'customer':             {'label': 'Became customer',      'color': '#34d399', 'bg': 'rgba(52,211,153,0.14)'},
    'paying_started':       {'label': 'Started paying',       'color': '#34d399', 'bg': 'rgba(52,211,153,0.14)'},
    'session_website':      {'label': 'Website',              'color': '#9aa3ad', 'bg': 'rgba(154,163,173,0.10)'},
    'session_portal':       {'label': 'Portal',               'color': '#34d399', 'bg': 'rgba(52,211,153,0.10)'},
}


def inject_global_css():
    st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
html,body,[class*="css"],.stApp {{
    font-family:'Inter',-apple-system,BlinkMacSystemFont,'Segoe UI',system-ui,sans-serif !important;
}}
.stApp {{ background:{T['bg']} !important; }}
.main .block-container {{
    background:{T['bg']} !important;
    padding-top:1.5rem !important;
    max-width:100% !important;
    padding-left:2rem !important;
    padding-right:2rem !important;
}}
[data-testid="stSidebar"] {{
    background:{T['bg2']} !important;
    border-right:1px solid {T['border']} !important;
}}
[data-testid="stSidebarNav"] {{ display:none !important; }}
[data-testid="stSidebar"] * {{ color:{T['textDim']} !important; }}
h1,h2,h3,h4,p {{ color:{T['text']}; margin:0; }}

/* Inputs */
.stTextInput>div>div>input {{
    background:{T['surface']} !important;
    color:{T['text']} !important;
    border:1px solid {T['border']} !important;
    border-radius:6px !important;
    font-family:'Inter',sans-serif !important;
    font-size:12px !important;
    padding:7px 10px 7px 30px !important;
}}
.stTextInput>div>div>input::placeholder {{ color:{T['textMute']} !important; }}
.stTextInput>div>div>input:focus {{
    border-color:{T['accent']} !important;
    box-shadow:none !important;
    outline:none !important;
}}

/* Selectbox */
.stSelectbox>div>div {{
    background:{T['surface']} !important;
    color:{T['text']} !important;
    border:1px solid {T['border']} !important;
    border-radius:6px !important;
    font-size:12px !important;
}}
.stSelectbox [data-baseweb="select"] {{ background:{T['surface']} !important; }}
.stSelectbox svg {{ fill:{T['textMute']} !important; }}

/* Buttons */
.stButton>button {{
    background:{T['surface']} !important;
    color:{T['textDim']} !important;
    border:1px solid {T['border']} !important;
    border-radius:6px !important;
    font-family:'Inter',sans-serif !important;
    font-size:12px !important;
    padding:6px 14px !important;
}}
.stButton>button:hover {{
    background:{T['surfaceHi']} !important;
    border-color:{T['borderHi']} !important;
    color:{T['text']} !important;
}}
.stButton>button[kind="primary"] {{
    background:{T['accentDim']} !important;
    color:{T['accent']} !important;
    border:1px solid rgba(74,222,128,0.3) !important;
}}
.stButton>button[kind="primary"]:hover {{
    background:rgba(74,222,128,0.2) !important;
}}

/* Radio (status filter) */
[data-testid="stRadio"]>div {{
    display:flex !important;
    gap:4px !important;
    background:{T['surface']} !important;
    border:1px solid {T['border']} !important;
    border-radius:6px !important;
    padding:3px !important;
    flex-wrap:nowrap !important;
}}
[data-testid="stRadio"] label {{
    background:transparent !important;
    color:{T['textDim']} !important;
    border-radius:4px !important;
    padding:5px 12px !important;
    font-size:11px !important;
    cursor:pointer !important;
    margin:0 !important;
    white-space:nowrap !important;
}}
[data-testid="stRadio"] label:has(input:checked) {{
    background:{T['surfaceHi']} !important;
    color:{T['text']} !important;
}}
[data-testid="stRadio"] [data-testid="stMarkdownContainer"] p {{
    font-size:11px !important;
    color:inherit !important;
}}
[data-testid="stRadio"] input {{ display:none !important; }}

/* Tabs */
.stTabs [data-baseweb="tab-list"] {{
    background:transparent !important;
    gap:0 !important;
    border-bottom:1px solid {T['border']} !important;
    padding:0 !important;
}}
.stTabs [data-baseweb="tab"] {{
    background:transparent !important;
    color:{T['textMute']} !important;
    font-size:12px !important;
    font-family:'Inter',sans-serif !important;
    padding:12px 0 !important;
    margin-right:24px !important;
    border-bottom:2px solid transparent !important;
    border-radius:0 !important;
}}
.stTabs [aria-selected="true"] {{
    color:{T['text']} !important;
    border-bottom:2px solid {T['accent']} !important;
    font-weight:500 !important;
}}
.stTabs [data-baseweb="tab-highlight"] {{ background:transparent !important; }}
.stTabs [data-baseweb="tab-panel"] {{
    background:transparent !important;
    padding:20px 0 0 0 !important;
}}

/* Metrics */
[data-testid="metric-container"] {{
    background:{T['surface']} !important;
    border:1px solid {T['border']} !important;
    border-radius:8px !important;
    padding:14px 16px !important;
}}
[data-testid="metric-container"]>label {{
    font-size:10px !important;
    letter-spacing:0.1em !important;
    color:{T['textMute']} !important;
    text-transform:uppercase !important;
}}
[data-testid="stMetricValue"] {{
    font-size:28px !important;
    font-weight:500 !important;
    letter-spacing:-0.02em !important;
    color:{T['text']} !important;
}}
[data-testid="stMetricDelta"] {{ font-size:11px !important; color:{T['textMute']} !important; }}
[data-testid="stMetricDeltaIcon-Up"],[data-testid="stMetricDeltaIcon-Down"] {{ display:none !important; }}

/* Expander */
[data-testid="stExpander"] details {{
    background:{T['surface']} !important;
    border:1px solid {T['border']} !important;
    border-radius:8px !important;
}}
[data-testid="stExpander"] summary {{
    color:{T['text']} !important;
    font-size:13px !important;
    font-weight:500 !important;
}}

/* Dataframe */
[data-testid="stDataFrame"] {{
    border:1px solid {T['border']} !important;
    border-radius:8px !important;
    overflow:hidden !important;
}}

/* Hide Streamlit chrome */
#MainMenu,footer,header {{ visibility:hidden !important; }}
[data-testid="stToolbar"] {{ display:none !important; }}
.block-container {{ padding-top:1rem !important; }}

/* Scrollbar */
::-webkit-scrollbar {{ width:8px; height:8px; }}
::-webkit-scrollbar-thumb {{ background:{T['bg3']}; border-radius:4px; }}
::-webkit-scrollbar-track {{ background:transparent; }}
hr {{ border-color:{T['border']} !important; margin:0 !important; }}
[data-testid="stHorizontalBlock"] {{ gap:12px !important; }}
</style>
""", unsafe_allow_html=True)


# ── HTML helpers ──────────────────────────────────────────────────────────────

def status_badge_html(status: str) -> str:
    m = STATUS_META.get(status, STATUS_META['lead'])
    return (
        f'<span style="display:inline-flex;align-items:center;gap:5px;'
        f'padding:2px 8px;border-radius:3px;font-size:10px;font-family:Inter,sans-serif;'
        f'font-weight:500;letter-spacing:0.08em;background:{m["bg"]};color:{m["color"]};'
        f'border:1px solid {m["color"]}22;">'
        f'<span style="width:5px;height:5px;border-radius:50%;background:{m["color"]};'
        f'display:inline-block;flex-shrink:0;"></span>{m["label"]}</span>'
    )


def channel_badge_html(channel: str) -> str:
    m = CHANNEL_META.get(channel, CHANNEL_META['Direct'])
    is_new = channel in ('Calendly', 'WebinarGeek')
    new_badge = (
        f'<span style="font-size:8px;padding:0 4px;border-radius:2px;'
        f'background:{m["dot"]};color:#0e1216;font-weight:700;'
        f'letter-spacing:0.05em;margin-left:2px;">NEW</span>'
    ) if is_new else ''
    return (
        f'<span style="display:inline-flex;align-items:center;gap:6px;'
        f'padding:2px 7px 2px 6px;border-radius:3px;font-size:11px;'
        f'font-family:Inter,sans-serif;background:{m["tint"]};color:{m["dot"]};'
        f'border:1px solid {m["dot"]}22;white-space:nowrap;">'
        f'<span style="width:5px;height:5px;border-radius:50%;background:{m["dot"]};'
        f'display:inline-block;flex-shrink:0;"></span>'
        f'<span>{channel}</span>{new_badge}</span>'
    )


def avatar_html(name: str, size: int = 28) -> str:
    parts = (name or '?').split()
    initials = ''.join(p[0] for p in parts if p)[:2].upper() or '?'
    fs = max(9, int(size * 0.38))
    return (
        f'<span style="display:inline-flex;align-items:center;justify-content:center;'
        f'width:{size}px;height:{size}px;border-radius:50%;'
        f'background:{T["accentDim"]};color:{T["accent"]};'
        f'font-size:{fs}px;font-weight:600;font-family:Inter,sans-serif;'
        f'letter-spacing:-0.02em;flex-shrink:0;'
        f'border:1px solid rgba(74,222,128,0.2);vertical-align:middle;">'
        f'{initials}</span>'
    )


def engagement_badges_html(forms: int = 0, webinars: int = 0, calls: int = 0) -> str:
    SVG_FORM = (
        '<svg width="12" height="12" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.5">'
        '<rect x="3" y="2.5" width="10" height="11" rx="1.5"/>'
        '<path d="M5.5 6H10.5M5.5 8.5H10.5M5.5 11H8.5" stroke-linecap="round"/></svg>'
    )
    SVG_VIDEO = (
        '<svg width="12" height="12" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.5">'
        '<rect x="2" y="4" width="9" height="8" rx="1.5"/>'
        '<path d="M11 7L14 5V11L11 9Z"/></svg>'
    )
    SVG_CAL = (
        '<svg width="12" height="12" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.5">'
        '<rect x="2.5" y="3.5" width="11" height="10" rx="1.5"/>'
        '<path d="M2.5 6.5H13.5M5.5 2V5M10.5 2V5" stroke-linecap="round"/></svg>'
    )
    chip = 'display:inline-flex;align-items:center;gap:4px;padding:2px 6px;border-radius:3px;font-size:10px;font-family:Inter,sans-serif;'
    items = []
    if forms > 0:
        items.append(f'<span title="Form submissions" style="{chip}background:{T["formDim"]};color:{T["form"]};border:1px solid {T["form"]}22;">{SVG_FORM}{forms}</span>')
    if webinars > 0:
        items.append(f'<span title="Webinar registrations" style="{chip}background:{T["webinarDim"]};color:{T["webinar"]};border:1px solid {T["webinar"]}22;">{SVG_VIDEO}{webinars}</span>')
    if calls > 0:
        items.append(f'<span title="Calendly bookings" style="{chip}background:{T["callDim"]};color:{T["call"]};border:1px solid {T["call"]}22;">{SVG_CAL}{calls}</span>')
    if not items:
        return f'<span style="font-size:11px;color:{T["textMute"]};">—</span>'
    return '<div style="display:flex;gap:5px;">' + ''.join(items) + '</div>'


def kpi_card_html(label: str, value: str, sub: str = '', color: str = '') -> str:
    val_color = color or T['text']
    sub_html = (
        f'<div style="font-size:11px;font-family:Inter,sans-serif;'
        f'color:{T["textMute"]};margin-top:4px;">{sub}</div>'
    ) if sub else ''
    return (
        f'<div style="background:{T["surface"]};border:1px solid {T["border"]};'
        f'border-radius:8px;padding:14px 16px;">'
        f'<div style="font-size:10px;font-family:Inter,sans-serif;color:{T["textMute"]};'
        f'letter-spacing:0.1em;margin-bottom:8px;text-transform:uppercase;">{label}</div>'
        f'<div style="font-size:28px;font-weight:500;letter-spacing:-0.02em;'
        f'color:{val_color};font-family:Inter,sans-serif;">{value}</div>'
        f'{sub_html}</div>'
    )


def section_label_html(text: str) -> str:
    return (
        f'<div style="font-size:10px;font-family:Inter,sans-serif;color:{T["textMute"]};'
        f'letter-spacing:0.1em;margin-bottom:10px;text-transform:uppercase;">{text}</div>'
    )


def detail_row_html(label: str, value, mono: bool = False) -> str:
    val_str = str(value) if value is not None and str(value) not in ('', 'None', 'nan', 'NaT') else '—'
    return (
        f'<div style="display:grid;grid-template-columns:160px 1fr;gap:16px;'
        f'padding:8px 16px;border-bottom:1px solid {T["border"]};align-items:center;">'
        f'<span style="font-size:11px;font-family:Inter,sans-serif;color:{T["textMute"]};'
        f'letter-spacing:0.03em;">{label}</span>'
        f'<span style="font-size:12px;font-family:Inter,sans-serif;color:{T["text"]};">{val_str}</span>'
        f'</div>'
    )


