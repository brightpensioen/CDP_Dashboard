import streamlit as st
import pandas as pd
from datetime import date, timedelta
from utils.data_loader import load_source_tracking
from components.ui import (
    T, inject_global_css, kpi_card_html, section_label_html,
    CHANNEL_META, channel_badge_html,
)
from components.charts import source_bar_chart, wow_comparison_chart


def render():
    inject_global_css()

    st.markdown(f"""
<div style="display:flex;align-items:baseline;gap:14px;margin-bottom:20px;">
  <h1 style="font-size:20px;font-weight:600;letter-spacing:-0.01em;color:{T['text']};">Source Tracking</h1>
  <span style="font-size:11px;font-family:Inter,sans-serif;color:{T['textMute']};letter-spacing:0.05em;">vw_source_tracking_enriched</span>
</div>
""", unsafe_allow_html=True)

    # Date range selector
    with st.sidebar:
        st.markdown(
            f'<div style="font-size:10px;font-family:Inter,sans-serif;color:{T["textMute"]};'
            f'letter-spacing:0.1em;text-transform:uppercase;margin-bottom:8px;">Date range</div>',
            unsafe_allow_html=True,
        )
        end_default   = date.today()
        start_default = end_default - timedelta(weeks=12)
        start_date = st.date_input('From', value=start_default, key='st_start')
        end_date   = st.date_input('To',   value=end_default,   key='st_end')

    if start_date > end_date:
        st.warning('Start date must be before end date.')
        return

    with st.spinner(''):
        df = load_source_tracking(str(start_date), str(end_date))

    if df is None or df.empty:
        st.info('No source tracking data for the selected period.')
        return

    # ── KPI row ──────────────────────────────────────────────────────────────
    prev_start = start_date - (end_date - start_date)
    with st.spinner(''):
        df_prev = load_source_tracking(str(prev_start), str(start_date))

    def _sum(df_, col):
        return int(df_[col].sum()) if col in df_.columns else 0

    total_users   = _sum(df, 'total_users')
    new_leads     = _sum(df, 'new_leads')
    new_customers = _sum(df, 'new_customers')
    new_churned   = _sum(df, 'new_churned')

    prev_users    = _sum(df_prev, 'total_users')    if df_prev is not None and not df_prev.empty else 0
    prev_leads    = _sum(df_prev, 'new_leads')      if df_prev is not None and not df_prev.empty else 0
    prev_cust     = _sum(df_prev, 'new_customers')  if df_prev is not None and not df_prev.empty else 0

    def _delta(cur, prev):
        if prev == 0:
            return None
        d = (cur - prev) / prev * 100
        return f"{'+'if d>=0 else ''}{d:.1f}% vs prev period"

    c1, c2, c3, c4 = st.columns(4)
    with c1: st.markdown(kpi_card_html('Total users',   f'{total_users:,}',   sub=_delta(total_users,   prev_users) or ''),  unsafe_allow_html=True)
    with c2: st.markdown(kpi_card_html('New leads',     f'{new_leads:,}',     sub=_delta(new_leads,     prev_leads) or '', color=T['lead']),     unsafe_allow_html=True)
    with c3: st.markdown(kpi_card_html('New customers', f'{new_customers:,}', sub=_delta(new_customers, prev_cust)  or '', color=T['customer']), unsafe_allow_html=True)
    with c4: st.markdown(kpi_card_html('Churned',       f'{new_churned:,}',                                                color='#f87171'),    unsafe_allow_html=True)

    st.markdown('<div style="height:20px;"></div>', unsafe_allow_html=True)

    # ── Tabs ─────────────────────────────────────────────────────────────────
    tab_leads, tab_customers, tab_trends, tab_rates = st.tabs([
        'Leads by source',
        'Customers by source',
        'WoW trends',
        'Conversion rates',
    ])

    with tab_leads:
        col_chart, col_table = st.columns([2, 3], gap='large')
        with col_chart:
            st.markdown(section_label_html('New leads by channel'), unsafe_allow_html=True)
            st.plotly_chart(
                source_bar_chart(df, 'new_leads', title=''),
                use_container_width=True,
                config={'displayModeBar': False},
            )
        with col_table:
            st.markdown(section_label_html('Weekly leads — channel × week'), unsafe_allow_html=True)
            _render_pivot(df, 'new_leads')

    with tab_customers:
        col_chart, col_table = st.columns([2, 3], gap='large')
        with col_chart:
            st.markdown(section_label_html('New customers by channel'), unsafe_allow_html=True)
            st.plotly_chart(
                source_bar_chart(df, 'new_customers', title=''),
                use_container_width=True,
                config={'displayModeBar': False},
            )
        with col_table:
            st.markdown(section_label_html('Weekly customers — channel × week'), unsafe_allow_html=True)
            _render_pivot(df, 'new_customers')

    with tab_trends:
        col_leads, col_customers = st.columns(2, gap='large')
        top6 = (
            df.groupby('initial_channel')['new_leads']
            .sum()
            .sort_values(ascending=False)
            .head(6)
            .index.tolist()
        )
        with col_leads:
            st.markdown(section_label_html('Leads — week over week'), unsafe_allow_html=True)
            st.plotly_chart(
                wow_comparison_chart(df, 'new_leads', top6),
                use_container_width=True,
                config={'displayModeBar': False},
            )
        with col_customers:
            st.markdown(section_label_html('Customers — week over week'), unsafe_allow_html=True)
            top6c = (
                df.groupby('initial_channel')['new_customers']
                .sum()
                .sort_values(ascending=False)
                .head(6)
                .index.tolist()
            )
            st.plotly_chart(
                wow_comparison_chart(df, 'new_customers', top6c),
                use_container_width=True,
                config={'displayModeBar': False},
            )

    with tab_rates:
        _render_rates(df)


# ── pivot table ───────────────────────────────────────────────────────────────

def _render_pivot(df: pd.DataFrame, metric: str) -> None:
    if 'activity_week' not in df.columns or 'initial_channel' not in df.columns:
        return
    pivot = (
        df.groupby(['initial_channel', 'activity_week'])[metric]
        .sum()
        .unstack('activity_week')
        .fillna(0)
        .astype(int)
    )
    pivot.columns = [pd.to_datetime(c).strftime('%b %d') for c in pivot.columns]
    pivot = pivot.sort_values(pivot.columns[-1], ascending=False)

    # Render as HTML table
    cols = list(pivot.columns)
    channel_col = f'font-size:11px;font-family:Inter,sans-serif;color:{T["textDim"]};padding:8px 12px;border-right:1px solid {T["border"]};'
    val_col     = f'font-size:11px;font-family:Inter,sans-serif;color:{T["textMute"]};padding:8px 10px;text-align:right;border-right:1px solid {T["border"]};'
    th_s        = f'font-size:10px;font-family:Inter,sans-serif;color:{T["textMute"]};letter-spacing:0.06em;text-transform:uppercase;padding:7px 10px;text-align:right;border-right:1px solid {T["border"]};background:{T["surface"]};'

    ncols = min(len(cols), 8)
    display_cols = cols[-ncols:]

    html = (
        f'<div style="overflow-x:auto;">'
        f'<table style="width:100%;border-collapse:collapse;background:{T["bg2"]};'
        f'border:1px solid {T["border"]};border-radius:8px;overflow:hidden;">'
        f'<thead><tr>'
        f'<th style="{th_s}text-align:left;min-width:140px;">Channel</th>'
    )
    for c in display_cols:
        html += f'<th style="{th_s}">{c}</th>'
    html += '</tr></thead><tbody>'

    for ch, row in pivot.iterrows():
        meta = CHANNEL_META.get(ch, {'dot': T['textMute']})
        html += (
            f'<tr style="border-top:1px solid {T["border"]};">'
            f'<td style="{channel_col}">'
            f'<div style="display:flex;align-items:center;gap:6px;">'
            f'<span style="width:5px;height:5px;border-radius:50%;background:{meta["dot"]};display:inline-block;flex-shrink:0;"></span>'
            f'<span>{ch}</span></div></td>'
        )
        for c in display_cols:
            val = int(row.get(c, 0))
            color = T['lead'] if val > 0 else T['textMute']
            html += f'<td style="{val_col}color:{color};">{val if val > 0 else "—"}</td>'
        html += '</tr>'

    html += '</tbody></table></div>'
    st.markdown(html, unsafe_allow_html=True)


# ── conversion rates ─────────────────────────────────────────────────────────

def _render_rates(df: pd.DataFrame) -> None:
    rate_cols = ['visitor_to_lead_rate', 'lead_to_signup_rate', 'signup_to_customer_rate', 'visitor_to_customer_rate']
    available = [c for c in rate_cols if c in df.columns]
    if not available:
        st.markdown(f'<div style="color:{T["textMute"]};font-size:12px;padding:20px 0;">No conversion rate data available.</div>', unsafe_allow_html=True)
        return

    agg = df.groupby('initial_channel')[available].mean().reset_index()
    agg = agg.sort_values(available[0] if available else available[0], ascending=False)

    cols_display = {
        'visitor_to_lead_rate':       'Visitor → Lead',
        'lead_to_signup_rate':        'Lead → Signup',
        'signup_to_customer_rate':    'Signup → Customer',
        'visitor_to_customer_rate':   'Visitor → Customer',
    }

    th_s = f'font-size:10px;font-family:Inter,sans-serif;color:{T["textMute"]};letter-spacing:0.06em;text-transform:uppercase;padding:7px 12px;text-align:right;border-right:1px solid {T["border"]};background:{T["surface"]};'
    td_s = f'font-size:11px;font-family:Inter,sans-serif;color:{T["textMute"]};padding:8px 12px;text-align:right;border-right:1px solid {T["border"]};'

    html = (
        f'<div style="overflow-x:auto;">'
        f'<table style="width:100%;border-collapse:collapse;background:{T["bg2"]};'
        f'border:1px solid {T["border"]};border-radius:8px;overflow:hidden;">'
        f'<thead><tr><th style="{th_s}text-align:left;min-width:140px;">Channel</th>'
    )
    for col in available:
        html += f'<th style="{th_s}">{cols_display.get(col, col)}</th>'
    html += '</tr></thead><tbody>'

    for _, r in agg.iterrows():
        ch = r['initial_channel']
        meta = CHANNEL_META.get(ch, {'dot': T['textMute']})
        html += (
            f'<tr style="border-top:1px solid {T["border"]};">'
            f'<td style="{td_s}text-align:left;">'
            f'<div style="display:flex;align-items:center;gap:6px;">'
            f'<span style="width:5px;height:5px;border-radius:50%;background:{meta["dot"]};display:inline-block;flex-shrink:0;"></span>'
            f'<span style="color:{T["textDim"]};">{ch}</span></div></td>'
        )
        for col in available:
            val = r.get(col, 0)
            pct_str = f'{val*100:.1f}%' if pd.notna(val) and val > 0 else '—'
            color   = T['customer'] if (pd.notna(val) and val > 0.1) else T['textMute']
            html += f'<td style="{td_s}color:{color};">{pct_str}</td>'
        html += '</tr>'

    html += '</tbody></table></div>'
    st.markdown(section_label_html('Avg. conversion rates by channel'), unsafe_allow_html=True)
    st.markdown(html, unsafe_allow_html=True)
