import plotly.graph_objects as go
import pandas as pd
from components.ui import T, CHANNEL_META, STATUS_META

CHANNEL_COLORS = {ch: m['dot'] for ch, m in CHANNEL_META.items()}
STATUS_COLORS  = {s: m['color'] for s, m in STATUS_META.items()}

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


def source_bar_chart(df: pd.DataFrame, metric: str, title: str = '', top_n: int = 10) -> go.Figure:
    agg = (
        df.groupby('initial_channel')[metric]
        .sum()
        .reset_index()
        .sort_values(metric, ascending=True)
        .tail(top_n)
    )
    colors = [CHANNEL_META.get(ch, {'dot': T['textMute']})['dot'] for ch in agg['initial_channel']]
    fig = go.Figure(go.Bar(
        x=agg[metric],
        y=agg['initial_channel'],
        orientation='h',
        marker_color=colors,
        text=agg[metric].astype(int),
        textposition='outside',
        textfont=dict(color=T['textDim'], size=11),
        hovertemplate='<b>%{y}</b><br>' + metric.replace('_', ' ').title() + ': %{x}<extra></extra>',
    ))
    h = max(len(agg) * 40 + 60, 200)
    fig.update_layout(
        **{k: v for k, v in DARK_LAYOUT.items() if k not in ('colorway', 'legend')},
        height=h,
        showlegend=False,
        title=dict(text=title, font=dict(size=13, color=T['textDim']), x=0),
        margin=dict(l=8, r=40, t=40, b=8),
        xaxis=dict(**DARK_LAYOUT['xaxis'], title=''),
        yaxis=dict(gridcolor='rgba(0,0,0,0)', linecolor='rgba(0,0,0,0)', tickfont=dict(size=11, color=T['textDim'])),
    )
    return fig


def wow_comparison_chart(df: pd.DataFrame, metric: str, top_channels: list) -> go.Figure:
    fig = go.Figure()
    for ch in top_channels:
        sub = df[df['initial_channel'] == ch].sort_values('activity_week')
        color = CHANNEL_META.get(ch, {'dot': T['textMute']})['dot']
        fig.add_trace(go.Scatter(
            name=ch,
            x=sub['activity_week'],
            y=sub[metric],
            mode='lines+markers',
            marker=dict(size=5, color=color),
            line=dict(color=color, width=2),
            hovertemplate=f'<b>{ch}</b><br>Week: %{{x|%b %d}}<br>{metric}: %{{y}}<extra></extra>',
        ))
    fig.update_layout(
        **{k: v for k, v in DARK_LAYOUT.items() if k != 'colorway'},
        hovermode='x unified',
        xaxis=dict(**DARK_LAYOUT['xaxis'], tickformat='%b %d'),
        yaxis=dict(**DARK_LAYOUT['yaxis']),
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


def form_submission_timeline(df_profiles: pd.DataFrame, start_date: str = '2026-01-01') -> go.Figure:
    df = df_profiles.dropna(subset=['first_submission_date']).copy()
    df = df[df['first_submission_date'] >= start_date]
    df['week'] = df['first_submission_date'].dt.to_period('W').dt.start_time
    agg = df.groupby(['week', 'first_form']).size().reset_index(name='count')
    top_forms = agg['first_form'].value_counts().head(4).index.tolist()

    palette = [T['form'], T['accent'], T['webinar'], T['call']]
    fig = go.Figure()
    for i, form in enumerate(top_forms):
        sub = agg[agg['first_form'] == form].sort_values('week')
        color = palette[i % len(palette)]
        fig.add_trace(go.Scatter(
            name=form,
            x=sub['week'],
            y=sub['count'],
            mode='lines',
            fill='tozeroy',
            line=dict(width=1.5, color=color),
            fillcolor=color.replace(')', ', 0.12)').replace('rgb', 'rgba') if 'rgb' in color else color + '1f',
            hovertemplate=f'<b>{form}</b><br>%{{y}}<extra></extra>',
        ))
    fig.update_layout(
        **{k: v for k, v in DARK_LAYOUT.items() if k != 'colorway'},
        xaxis=dict(**DARK_LAYOUT['xaxis'], tickformat='%b %d'),
        yaxis=dict(**DARK_LAYOUT['yaxis']),
    )
    return fig
