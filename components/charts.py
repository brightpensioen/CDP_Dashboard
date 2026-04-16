"""
Plotly chart factories for the CDP dashboard.
All charts use a consistent dark theme.
"""

import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
from components.ui import CHANNEL_COLORS, STATUS_COLORS

# ── shared theme ────────────────────────────────────────────────────────────

DARK_LAYOUT = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(family="DM Mono, monospace", color="rgba(255,255,255,0.6)", size=11),
    margin=dict(l=8, r=8, t=32, b=8),
    legend=dict(
        orientation="h",
        yanchor="bottom",
        y=1.02,
        xanchor="left",
        x=0,
        font=dict(size=11),
        bgcolor="rgba(0,0,0,0)",
    ),
    xaxis=dict(
        gridcolor="rgba(255,255,255,0.05)",
        linecolor="rgba(255,255,255,0.08)",
        tickcolor="rgba(255,255,255,0.08)",
        tickfont=dict(size=10),
    ),
    yaxis=dict(
        gridcolor="rgba(255,255,255,0.05)",
        linecolor="rgba(0,0,0,0)",
        tickfont=dict(size=10),
        zeroline=False,
    ),
    colorway=list(CHANNEL_COLORS.values()),
    hoverlabel=dict(
        bgcolor="#12121f",
        bordercolor="rgba(255,255,255,0.15)",
        font_color="#f0ede4",
        font_size=12,
    ),
)


def _apply_dark(fig: go.Figure, title: str = "") -> go.Figure:
    fig.update_layout(title=dict(text=title, font=dict(size=13, color="rgba(255,255,255,0.6)"), x=0), **DARK_LAYOUT)
    return fig


# ── charts ───────────────────────────────────────────────────────────────────

def weekly_growth_chart(df_growth: pd.DataFrame, start_date: str = "2026-03-01") -> go.Figure:
    """
    Stacked bar chart: new profiles per week, split by status.
    df_growth columns: week, status, new_profiles
    """
    df_growth = df_growth[df_growth["week"] >= start_date]
    fig = go.Figure()
    for status, color in STATUS_COLORS.items():
        sub = df_growth[df_growth["status"] == status].sort_values("week")
        fig.add_trace(go.Bar(
            name=status.capitalize(),
            x=sub["week"],
            y=sub["new_profiles"],
            marker_color=color,
            hovertemplate=f"<b>{status.capitalize()}</b><br>Week: %{{x|%b %d}}<br>New: %{{y}}<extra></extra>",
        ))
    fig.update_layout(
        barmode="stack",
        **{k: v for k, v in DARK_LAYOUT.items() if k != "colorway"},
    )
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=DARK_LAYOUT["font"],
        margin=dict(l=8, r=8, t=36, b=8),
        legend=DARK_LAYOUT["legend"],
        hoverlabel=DARK_LAYOUT["hoverlabel"],
        title_text="",
        xaxis=dict(**DARK_LAYOUT["xaxis"], dtick="M1", tickformat="%b %d"),
        yaxis=dict(**DARK_LAYOUT["yaxis"], title="New profiles"),
    )
    return fig


def source_bar_chart(
    df: pd.DataFrame,
    metric: str,
    title: str,
    top_n: int = 10,
) -> go.Figure:
    """
    Horizontal bar chart for a given metric (new_leads or new_customers) by channel.
    df columns: initial_channel, {metric}
    """
    agg = (
        df.groupby("initial_channel")[metric]
        .sum()
        .reset_index()
        .sort_values(metric, ascending=True)
        .tail(top_n)
    )
    colors = [CHANNEL_COLORS.get(ch, "#888780") for ch in agg["initial_channel"]]

    fig = go.Figure(go.Bar(
        x=agg[metric],
        y=agg["initial_channel"],
        orientation="h",
        marker_color=colors,
        text=agg[metric].astype(int),
        textposition="outside",
        hovertemplate="<b>%{y}</b><br>" + metric.replace("_", " ").title() + ": %{x}<extra></extra>",
    ))
    h = max(len(agg) * 40 + 60, 200)
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=DARK_LAYOUT["font"],
        margin=dict(l=8, r=40, t=40, b=8),
        hoverlabel=DARK_LAYOUT["hoverlabel"],
        title=dict(text=title, font=dict(size=13, color="rgba(255,255,255,0.6)"), x=0),
        height=h,
        xaxis=dict(**DARK_LAYOUT["xaxis"], title=""),
        yaxis=dict(
            gridcolor="rgba(0,0,0,0)",
            linecolor="rgba(0,0,0,0)",
            tickfont=dict(size=11),
        ),
        showlegend=False,
    )
    return fig


def wow_comparison_chart(df: pd.DataFrame, metric: str, top_channels: list[str]) -> go.Figure:
    """
    Line chart: selected metric by week, one line per channel.
    df columns: activity_week, initial_channel, {metric}
    """
    fig = go.Figure()
    for ch in top_channels:
        sub = df[df["initial_channel"] == ch].sort_values("activity_week")
        fig.add_trace(go.Scatter(
            name=ch,
            x=sub["activity_week"],
            y=sub[metric],
            mode="lines+markers",
            marker=dict(size=6),
            line=dict(color=CHANNEL_COLORS.get(ch, "#888780"), width=2),
            hovertemplate=f"<b>{ch}</b><br>Week: %{{x|%b %d}}<br>{metric}: %{{y}}<extra></extra>",
        ))
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=DARK_LAYOUT["font"],
        margin=dict(l=8, r=8, t=50, b=8),
        legend=DARK_LAYOUT["legend"],
        hoverlabel=DARK_LAYOUT["hoverlabel"],
        hovermode="x unified",
        title_text="",
        xaxis=dict(**DARK_LAYOUT["xaxis"], dtick=7 * 24 * 3600 * 1000, tickformat="%b %d"),
        yaxis=dict(**DARK_LAYOUT["yaxis"]),
    )
    return fig


def status_donut(counts: dict) -> go.Figure:
    """
    Donut chart for profile status distribution.
    counts: {status: count}
    """
    labels = list(counts.keys())
    values = list(counts.values())
    colors = [STATUS_COLORS.get(l, "#888780") for l in labels]

    fig = go.Figure(go.Pie(
        labels=[l.capitalize() for l in labels],
        values=values,
        hole=0.65,
        marker=dict(colors=colors, line=dict(color="rgba(0,0,0,0)", width=0)),
        textinfo="none",
        hovertemplate="<b>%{label}</b><br>Count: %{value}<br>Share: %{percent}<extra></extra>",
    ))
    total = sum(values)
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=DARK_LAYOUT["font"],
        margin=dict(l=0, r=0, t=0, b=0),
        showlegend=False,
        annotations=[dict(
            text=f"<b>{total}</b><br>profiles",
            x=0.5, y=0.5,
            font=dict(size=16, color="#f0ede4"),
            showarrow=False,
        )],
        hoverlabel=DARK_LAYOUT["hoverlabel"],
    )
    return fig


def conversion_funnel(visitors: int, leads: int, signups: int, customers: int) -> go.Figure:
    """
    Funnel chart for visitor → lead → signup → customer.
    """
    fig = go.Figure(go.Funnel(
        y=["Visitors", "Leads", "Signed up", "Customers"],
        x=[visitors, leads, signups, customers],
        marker=dict(color=["#378ADD", "#85B7EB", "#e8a838", "#1d9e75"]),
        textinfo="value+percent previous",
        textfont=dict(color="#f0ede4", size=12),
        hovertemplate="<b>%{y}</b><br>Count: %{x}<extra></extra>",
    ))
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=DARK_LAYOUT["font"],
        margin=dict(l=100, r=8, t=8, b=8),
        hoverlabel=DARK_LAYOUT["hoverlabel"],
        showlegend=False,
    )
    return fig


def form_submission_timeline(df_profiles: pd.DataFrame, start_date: str = "2026-03-01") -> go.Figure:
    """
    Area chart: form submissions per week aggregated from first/last submission dates.
    Uses first_submission_date bucketed by week.
    """
    df = df_profiles.dropna(subset=["first_submission_date"]).copy()
    df = df[df["first_submission_date"] >= start_date]
    df["week"] = df["first_submission_date"].dt.to_period("W").dt.start_time
    agg = df.groupby(["week", "first_form"]).size().reset_index(name="count")
    forms = agg["first_form"].value_counts().head(3).index.tolist()

    fig = go.Figure()
    for form in forms:
        sub = agg[agg["first_form"] == form].sort_values("week")
        fig.add_trace(go.Scatter(
            name=form,
            x=sub["week"],
            y=sub["count"],
            mode="lines",
            fill="tozeroy",
            line=dict(width=1.5),
            opacity=0.7,
            hovertemplate=f"<b>{form}</b><br>Week: %{{x|%b %d}}<br>Count: %{{y}}<extra></extra>",
        ))
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=DARK_LAYOUT["font"],
        margin=dict(l=8, r=8, t=40, b=8),
        legend=DARK_LAYOUT["legend"],
        hoverlabel=DARK_LAYOUT["hoverlabel"],
        title=dict(text="Form submissions by week", font=dict(size=13, color="rgba(255,255,255,0.6)"), x=0),
        xaxis=dict(**DARK_LAYOUT["xaxis"], dtick="M1", tickformat="%b %d"),
        yaxis=dict(**DARK_LAYOUT["yaxis"]),
    )
    return fig
