import streamlit as st
import pandas as pd
from utils.data_loader import load_profiles, load_profile_growth
from components.ui import (
    T, inject_global_css, kpi_card_html, section_label_html,
    STATUS_META, status_badge_html, channel_badge_html, avatar_html,
)
from components.charts import weekly_growth_chart, status_donut, conversion_funnel


def render():
    inject_global_css()

    st.markdown(f"""
<div style="display:flex;align-items:baseline;gap:14px;margin-bottom:20px;">
  <h1 style="font-size:20px;font-weight:600;letter-spacing:-0.01em;color:{T['text']};">Overview</h1>
  <span style="font-size:11px;font-family:Inter,sans-serif;color:{T['textMute']};letter-spacing:0.05em;">CDP health</span>
</div>
""", unsafe_allow_html=True)

    with st.spinner(''):
        df = load_profiles()
        df_growth = load_profile_growth()

    if df is None or df.empty:
        st.error('No data available.')
        return

    total     = len(df)
    customers = int((df['status'] == 'customer').sum())
    leads     = int((df['status'] == 'lead').sum())
    signed    = int((df['status'] == 'signed-up').sum())
    churned   = int((df['status'] == 'churned').sum()) if 'churned' in df['status'].values else 0

    # KPI cards
    c1, c2, c3, c4, c5 = st.columns(5)
    with c1: st.markdown(kpi_card_html('Total profiles', f'{total:,}'),                       unsafe_allow_html=True)
    with c2: st.markdown(kpi_card_html('Customers',      f'{customers:,}', color=T['customer']),  unsafe_allow_html=True)
    with c3: st.markdown(kpi_card_html('Leads',          f'{leads:,}',     color=T['lead']),      unsafe_allow_html=True)
    with c4: st.markdown(kpi_card_html('Signed up',      f'{signed:,}',    color=T['signed']),    unsafe_allow_html=True)
    with c5: st.markdown(kpi_card_html('Churned',        f'{churned:,}',   color='#f87171'),      unsafe_allow_html=True)

    st.markdown('<div style="height:20px;"></div>', unsafe_allow_html=True)

    # Growth chart + donut
    col_growth, col_donut = st.columns([3, 1], gap='large')

    with col_growth:
        st.markdown(section_label_html('Profile growth (weekly)'), unsafe_allow_html=True)
        if df_growth is not None and not df_growth.empty:
            cutoff = (pd.Timestamp.now() - pd.DateOffset(months=6)).strftime('%Y-%m-%d')
            st.plotly_chart(
                weekly_growth_chart(df_growth, start_date=cutoff),
                use_container_width=True,
                config={'displayModeBar': False},
            )
        else:
            st.markdown(f'<div style="color:{T["textMute"]};font-size:12px;padding:20px 0;">No growth data available.</div>', unsafe_allow_html=True)

    with col_donut:
        st.markdown(section_label_html('Status distribution'), unsafe_allow_html=True)
        counts = df['status'].value_counts().to_dict()
        st.plotly_chart(status_donut(counts), use_container_width=True, config={'displayModeBar': False})

        legend_html = ''
        for status, meta in STATUS_META.items():
            cnt = counts.get(status, 0)
            if cnt == 0:
                continue
            pct = cnt / total * 100 if total else 0
            legend_html += (
                f'<div style="display:flex;align-items:center;justify-content:space-between;'
                f'padding:4px 0;border-bottom:1px solid {T["border"]};">'
                f'<div style="display:flex;align-items:center;gap:8px;">'
                f'<span style="width:7px;height:7px;border-radius:50%;background:{meta["color"]};display:inline-block;"></span>'
                f'<span style="font-size:11px;font-family:Inter,sans-serif;color:{T["textDim"]};">{meta["label"]}</span>'
                f'</div>'
                f'<div style="display:flex;align-items:center;gap:10px;">'
                f'<span style="font-size:11px;color:{T["textMute"]};font-family:Inter,sans-serif;">{pct:.0f}%</span>'
                f'<span style="font-size:11px;font-family:Inter,sans-serif;color:{T["textDim"]};font-weight:500;">{cnt:,}</span>'
                f'</div></div>'
            )
        st.markdown(f'<div style="margin-top:4px;">{legend_html}</div>', unsafe_allow_html=True)

    st.markdown('<div style="height:20px;"></div>', unsafe_allow_html=True)

    # Funnel + Health
    col_funnel, col_health = st.columns([1, 1], gap='large')

    with col_funnel:
        st.markdown(section_label_html('Acquisition funnel'), unsafe_allow_html=True)
        has_signup = int(df['has_signed_up'].sum()) if 'has_signed_up' in df.columns else 0
        st.plotly_chart(
            conversion_funnel(total, leads, has_signup, customers),
            use_container_width=True,
            config={'displayModeBar': False},
        )

    with col_health:
        st.markdown(section_label_html('CDP health checks'), unsafe_allow_html=True)

        def health_row(label: str, ok: bool, detail: str = '') -> str:
            color  = T['customer'] if ok else '#f87171'
            icon   = '✓' if ok else '✗'
            bg     = 'rgba(52,211,153,0.08)' if ok else 'rgba(248,113,113,0.08)'
            border = 'rgba(52,211,153,0.2)'  if ok else 'rgba(248,113,113,0.2)'
            det = (f'<div style="font-size:11px;font-family:Inter,sans-serif;color:{T["textMute"]};margin-top:2px;">{detail}</div>') if detail else ''
            return (
                f'<div style="display:flex;align-items:flex-start;gap:10px;padding:10px 14px;'
                f'background:{bg};border:1px solid {border};border-radius:6px;margin-bottom:6px;">'
                f'<span style="font-size:13px;color:{color};font-weight:600;flex-shrink:0;margin-top:1px;">{icon}</span>'
                f'<div><div style="font-size:12px;font-family:Inter,sans-serif;color:{T["text"]};font-weight:500;">{label}</div>{det}</div>'
                f'</div>'
            )

        ch_ok     = df['initial_channel'].notna().mean() > 0.9 if 'initial_channel' in df.columns else False
        form_ok   = 'form_submissions' in df.columns and df['form_submissions'].notna().any()
        das_ok    = 'das_id' in df.columns and df['das_id'].notna().any()
        no_dupes  = df['Email'].duplicated().sum() == 0
        fresh_ok  = True
        if 'last_updated_at' in df.columns and df['last_updated_at'].notna().any():
            latest = pd.to_datetime(df['last_updated_at']).max()
            try:
                if latest.tzinfo is None:
                    latest = latest.tz_localize('UTC')
                fresh_ok = (pd.Timestamp.now(tz='UTC') - latest).days < 2
            except Exception:
                pass

        ch_pct = f'{df["initial_channel"].notna().mean()*100:.0f}% of profiles have a channel' if 'initial_channel' in df.columns else ''
        form_n  = f'{int(df["form_submissions"].gt(0).sum())} profiles with ≥1 form' if form_ok else ''
        das_n   = f'{int(df["das_id"].notna().sum())} profiles linked to DAS' if das_ok else ''
        dup_n   = f'{df["Email"].duplicated().sum()} duplicate email(s) found'
        fresh_n = 'Updated within last 48 h'

        st.markdown(
            health_row('Channel data populated',    ch_ok,    ch_pct) +
            health_row('Form submission data',       form_ok,  form_n) +
            health_row('DAS linkage active',         das_ok,   das_n) +
            health_row('No duplicate emails',        no_dupes, dup_n) +
            health_row('Data freshness',             fresh_ok, fresh_n),
            unsafe_allow_html=True,
        )

    st.markdown('<div style="height:20px;"></div>', unsafe_allow_html=True)

    # Recent profiles
    st.markdown(section_label_html('Recent profiles'), unsafe_allow_html=True)
    recent = df.sort_values('profile_date', ascending=False).head(10)

    grid = '2fr 100px 110px 180px 130px'
    th   = f'font-size:10px;font-family:Inter,sans-serif;color:{T["textMute"]};letter-spacing:0.08em;text-transform:uppercase;'
    rs   = f'display:grid;grid-template-columns:{grid};gap:12px;padding:10px 14px;border-bottom:1px solid {T["border"]};align-items:center;'

    table = (
        f'<div style="display:grid;grid-template-columns:{grid};padding:8px 14px;gap:12px;'
        f'align-items:center;background:{T["surface"]};border:1px solid {T["border"]};border-radius:8px 8px 0 0;">'
        f'<div style="{th}">Email</div><div style="{th}">Status</div>'
        f'<div style="{th}">Profile date</div><div style="{th}">Channel</div>'
        f'<div style="{th}">Location</div></div>'
        f'<div style="background:{T["bg2"]};border:1px solid {T["border"]};border-top:none;border-radius:0 0 8px 8px;overflow:hidden;">'
    )

    for _, r in recent.iterrows():
        fn   = str(r.get('das_first_name') or '').strip()
        ln   = str(r.get('das_last_name')  or '').strip()
        name = f'{fn} {ln}'.strip() or r['Email'].split('@')[0].replace('.', ' ').title()
        ch   = str(r.get('initial_channel') or 'Direct')
        loc  = ', '.join(filter(None, [str(r.get('initial_city') or ''), str(r.get('initial_country') or '')]))[:22] or '—'
        try:
            date_str = pd.to_datetime(r.get('profile_date')).strftime('%Y-%m-%d')
        except Exception:
            date_str = '—'

        table += (
            f'<div style="{rs}">'
            f'<div style="display:flex;align-items:center;gap:10px;min-width:0;">'
            f'{avatar_html(name, 22)}'
            f'<span style="font-size:12px;font-family:Inter,sans-serif;color:{T["text"]};'
            f'overflow:hidden;text-overflow:ellipsis;white-space:nowrap;">{r["Email"]}</span>'
            f'</div>'
            f'<div>{status_badge_html(r.get("status","lead"))}</div>'
            f'<div style="font-size:11px;font-family:Inter,sans-serif;color:{T["textDim"]};">{date_str}</div>'
            f'<div>{channel_badge_html(ch)}</div>'
            f'<div style="font-size:11px;font-family:Inter,sans-serif;color:{T["textDim"]};">{loc}</div>'
            f'</div>'
        )

    table += '</div>'
    st.markdown(table, unsafe_allow_html=True)
