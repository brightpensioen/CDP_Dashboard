import plotly.graph_objects as go
import pandas as pd
from components.ui import T, CHANNEL_META, STATUS_META

STATUS_COLORS = {s: m['color'] for s, m in STATUS_META.items()}

DARK_LAYOUT = dict(
    paper_bgcolor='rgba(0,0,0,0)',
    plot_bgcolor='rgba(0,0,0,0)',
    font=dict(family='Inter, sans-serif', color=T['textDim'], size=11),
    margin=dict(l=8, r=8, t=32, b=8),
    legend=dict(
        orientation='h',
        yanchor='bottom', y=1.02,
        xanchor='left', x=0,
        font=dict(size=11),
        bgcolor='rgba(0,0,0,0)',
    ),
    xaxis=dict(
        gridcolor=T['border'],
        linecolor=T['border'],
        tickcolor=T['border'],
        tickfont=dict(size=10, color=T['textMute']),
    ),
    yaxis=dict(
        gridcolor=T['border'],
        linecolor='rgba(0,0,0,0)',
        tickfont=dict(size=10, color=T['textMute']),
        zeroline=False,
    ),
    hoverlabel=dict(
        bgcolor=T['surface'],
        bordercolor=T['borderHi'],
        font_color=T['text'],
        font_size=12,
    ),
)


def weekly_growth_chart(df_growth: pd.DataFrame, start_date: str = '2026-01-01') -> go.Figure:
    df_growth = df_growth[df_growth['week'] >= start_date]
    fig = go.Figure()
    order = ['customer', 'signed-up', 'lead', 'churned']
    for status in order:
        color = STATUS_COLORS.get(status, T['textMute'])
        sub = df_growth[df_growth['status'] == status].sort_values('week')
        if sub.empty:
            continue
        fig.add_trace(go.Bar(
            name=STATUS_META.get(status, {}).get('label', status.title()),
            x=sub['week'],
            y=sub['new_profiles'],
            marker_color=color,
            hovertemplate=f'<b>{status.title()}</b><br>Week: %{{x|%b %d}}<br>New: %{{y}}<extra></extra>',
        ))
    fig.update_layout(
        barmode='stack',
        **{k: v for k, v in DARK_LAYOUT.items() if k != 'colorway'},
        xaxis=dict(**DARK_LAYOUT['xaxis'], tickformat='%b %d'),
        yaxis=dict(**DARK_LAYOUT['yaxis'], title=''),
    )
    return fig


def status_donut(counts: dict) -> go.Figure:
    labels = list(counts.keys())
    values = list(counts.values())
    colors = [STATUS_COLORS.get(l, T['textMute']) for l in labels]
    fig = go.Figure(go.Pie(
        labels=[STATUS_META.get(l, {}).get('label', l.title()) for l in labels],
        values=values,
        hole=0.65,
        marker=dict(colors=colors, line=dict(color=T['bg'], width=2)),
        textinfo='none',
        hovertemplate='<b>%{label}</b><br>%{value:,}<br>%{percent}<extra></extra>',
    ))
    total = sum(values)
    fig.update_layout(
        **{k: v for k, v in DARK_LAYOUT.items() if k not in ('colorway', 'xaxis', 'yaxis', 'legend')},
        showlegend=False,
        margin=dict(l=0, r=0, t=0, b=0),
        annotations=[dict(
            text=f'<b>{total:,}</b><br><span style="font-size:11px">total</span>',
            x=0.5, y=0.5,
            font=dict(size=20, color=T['text']),
            showarrow=False,
        )],
    )
    return fig


def conversion_funnel(visitors: int, leads: int, signups: int, customers: int) -> go.Figure:
    fig = go.Figure(go.Funnel(
        y=['Visitors', 'Leads', 'Signed up', 'Customers'],
        x=[visitors, leads, signups, customers],
        marker=dict(color=[T['textMute'], T['lead'], T['signed'], T['customer']]),
        textinfo='value+percent previous',
        textfont=dict(color=T['text'], size=12),
        hovertemplate='<b>%{y}</b><br>Count: %{x}<extra></extra>',
    ))
    fig.update_layout(
        **{k: v for k, v in DARK_LAYOUT.items() if k not in ('colorway', 'xaxis', 'yaxis', 'legend')},
        margin=dict(l=100, r=8, t=8, b=8),
        showlegend=False,
    )
    return fig


