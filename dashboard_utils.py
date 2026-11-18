"""
SupeRR Selector Season 2 — Dashboard Utility Functions
Helper modules for data caching, styling, and interactive Plotly visualizations.
"""

import os
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go

# Color Constants (Rajasthan Royals Theme)
RR_PINK = "#D91E5B"
RR_PINK_LIGHT = "#FF2E93"
RR_BLUE = "#1E88E5"
RR_BLUE_LIGHT = "#60A5FA"
RR_NAVY_DARK = "#0A0F1D"
RR_NAVY_CARD = "#151E33"
RR_NAVY_BORDER = "#25334D"
RR_GOLD = "#F59E0B"
RR_GREEN = "#10B981"
RR_WHITE = "#F8FAFC"
RR_MUTED = "#94A3B8"

@st.cache_data
def load_data(output_dir: str = "outputs"):
    """
    Loads all precomputed analytics engine outputs from the outputs directory.
    Uses st.cache_data for instantaneous page responsiveness.
    """
    data = {}
    
    files = {
        'top10_batters': 'top10_batters_pressure.csv',
        'top10_bowlers': 'top10_bowlers_pressure.csv',
        'all_batters': 'all_batters_ppi.csv',
        'all_bowlers': 'all_bowlers_ppi.csv',
        'case_studies': 'pressure_case_studies.csv',
        'sensitivity': 'sensitivity_analysis.csv',
        'batter_stats': 'batter_statistics.csv',
        'bowler_stats': 'bowler_statistics.csv',
        'data_quality': 'data_quality_report.csv'
    }
    
    for key, filename in files.items():
        path = os.path.join(output_dir, filename)
        if os.path.exists(path):
            data[key] = pd.read_csv(path)
        else:
            data[key] = pd.DataFrame()
            
    # Load validation report text
    val_path = os.path.join(output_dir, 'validation_report.txt')
    if os.path.exists(val_path):
        with open(val_path, 'r', encoding='utf-8', errors='ignore') as f:
            data['validation_text'] = f.read()
    else:
        data['validation_text'] = "Validation report not found."
        
    return data


def apply_custom_css():
    """
    Injects custom CSS styling inspired by the Rajasthan Royals aesthetic:
    Dark navy background, hot pink and royal blue accents, crisp typography.
    """
    st.markdown(f"""
    <style>
        /* Base Page Background */
        .stApp {{
            background-color: {RR_NAVY_DARK};
            color: {RR_WHITE};
            font-family: 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
        }}
        
        /* Sidebar Styling */
        section[data-testid="stSidebar"] {{
            background-color: #0d1527;
            border-right: 1px solid {RR_NAVY_BORDER};
        }}
        section[data-testid="stSidebar"] .stMarkdown h1, 
        section[data-testid="stSidebar"] .stMarkdown h2, 
        section[data-testid="stSidebar"] .stMarkdown h3 {{
            color: {RR_PINK};
        }}
        
        /* Metric Card Container */
        .rr-card {{
            background-color: {RR_NAVY_CARD};
            border: 1px solid {RR_NAVY_BORDER};
            border-radius: 12px;
            padding: 20px;
            margin-bottom: 16px;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.25);
            transition: transform 0.2s ease, border-color 0.2s ease;
        }}
        .rr-card:hover {{
            transform: translateY(-2px);
            border-color: {RR_PINK};
        }}
        
        .rr-card-title {{
            font-size: 0.82rem;
            text-transform: uppercase;
            letter-spacing: 0.08em;
            color: {RR_MUTED};
            margin-bottom: 6px;
            font-weight: 600;
        }}
        
        .rr-card-value {{
            font-size: 2.1rem;
            font-weight: 700;
            color: {RR_WHITE};
            margin-bottom: 4px;
            line-height: 1.1;
        }}
        
        .rr-card-subtitle {{
            font-size: 0.85rem;
            color: {RR_BLUE_LIGHT};
        }}
        
        .rr-card-pink {{
            border-left: 4px solid {RR_PINK};
        }}
        
        .rr-card-blue {{
            border-left: 4px solid {RR_BLUE};
        }}
        
        .rr-card-gold {{
            border-left: 4px solid {RR_GOLD};
        }}

        /* Section Headings */
        h1, h2, h3 {{
            color: {RR_WHITE};
            font-weight: 700;
        }}
        
        .rr-badge-pink {{
            background-color: rgba(217, 30, 91, 0.18);
            color: {RR_PINK_LIGHT};
            border: 1px solid {RR_PINK};
            border-radius: 6px;
            padding: 3px 8px;
            font-size: 0.78rem;
            font-weight: 600;
            display: inline-block;
        }}

        .rr-badge-blue {{
            background-color: rgba(30, 136, 229, 0.18);
            color: {RR_BLUE_LIGHT};
            border: 1px solid {RR_BLUE};
            border-radius: 6px;
            padding: 3px 8px;
            font-size: 0.78rem;
            font-weight: 600;
            display: inline-block;
        }}

        .rr-badge-gold {{
            background-color: rgba(245, 158, 11, 0.18);
            color: {RR_GOLD};
            border: 1px solid {RR_GOLD};
            border-radius: 6px;
            padding: 3px 8px;
            font-size: 0.78rem;
            font-weight: 600;
            display: inline-block;
        }}

        /* Buttons */
        .stButton>button {{
            background: linear-gradient(135deg, {RR_PINK} 0%, #ad1457 100%);
            color: white;
            border: none;
            border-radius: 8px;
            padding: 8px 18px;
            font-weight: 600;
            transition: all 0.2s ease;
        }}
        .stButton>button:hover {{
            background: linear-gradient(135deg, {RR_PINK_LIGHT} 0%, {RR_PINK} 100%);
            box-shadow: 0 4px 12px rgba(217, 30, 91, 0.4);
            color: white;
        }}

        /* Download button styling */
        .stDownloadButton>button {{
            background: linear-gradient(135deg, #1e3a8a 0%, {RR_BLUE} 100%);
            color: white;
            border: none;
            border-radius: 8px;
            font-weight: 600;
        }}
        .stDownloadButton>button:hover {{
            background: linear-gradient(135deg, {RR_BLUE} 0%, {RR_BLUE_LIGHT} 100%);
            box-shadow: 0 4px 12px rgba(30, 136, 229, 0.4);
            color: white;
        }}
        
        /* Table styling */
        div[data-testid="stDataFrame"] {{
            border: 1px solid {RR_NAVY_BORDER};
            border-radius: 8px;
            overflow: hidden;
        }}

        /* Tabs */
        .stTabs [data-baseweb="tab-list"] {{
            gap: 8px;
        }}
        .stTabs [data-baseweb="tab"] {{
            background-color: {RR_NAVY_CARD};
            border-radius: 6px 6px 0px 0px;
            padding: 8px 16px;
            border: 1px solid {RR_NAVY_BORDER};
            color: {RR_MUTED};
        }}
        .stTabs [aria-selected="true"] {{
            background-color: {RR_PINK} !important;
            color: white !important;
            border-color: {RR_PINK} !important;
        }}
    </style>
    """, unsafe_allow_html=True)


def render_metric_card(title: str, value: str, subtitle: str = "", card_type: str = "pink"):
    """
    Renders an HTML metric card with Rajasthan Royals design.
    """
    border_class = f"rr-card-{card_type}"
    st.markdown(f"""
    <div class="rr-card {border_class}">
        <div class="rr-card-title">{title}</div>
        <div class="rr-card-value">{value}</div>
        <div class="rr-card-subtitle">{subtitle}</div>
    </div>
    """, unsafe_allow_html=True)


def create_top10_bar_chart(df: pd.DataFrame, is_batter: bool = True):
    """
    Creates an interactive horizontal bar chart for the Top 10 PPI performers.
    """
    player_col = 'striker_name' if is_batter else 'bowler_name'
    title = "Top 10 Batters — Pressure Performance Index (PPI)" if is_batter else "Top 10 Bowlers — Pressure Performance Index (PPI)"
    color_scale = [[0, '#3b82f6'], [1, RR_PINK]] if is_batter else [[0, '#06b6d4'], [1, RR_BLUE]]
    
    # Sort ascending for horizontal bar chart display
    plot_df = df.sort_values('ppi_score', ascending=True).copy()
    
    fig = px.bar(
        plot_df,
        x='ppi_score',
        y=player_col,
        orientation='h',
        text='ppi_score',
        title=title,
        color='ppi_score',
        color_continuous_scale=color_scale,
        labels={'ppi_score': 'PPI Score (40-100)', player_col: 'Player'}
    )
    
    fig.update_traces(
        texttemplate='%{text:.2f}',
        textposition='outside',
        marker_line_width=1,
        marker_line_color=RR_NAVY_BORDER,
        hovertemplate="<b>%{y}</b><br>PPI Score: %{x:.2f}<extra></extra>"
    )
    
    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor=RR_NAVY_CARD,
        plot_bgcolor=RR_NAVY_CARD,
        font=dict(color=RR_WHITE, family="Segoe UI, sans-serif"),
        height=450,
        margin=dict(l=20, r=40, t=50, b=30),
        xaxis=dict(range=[35, 105], showgrid=True, gridcolor="#223048"),
        yaxis=dict(showgrid=False),
        coloraxis_showscale=False
    )
    
    return fig


def create_batter_scatter_chart(all_batters: pd.DataFrame, top10_batters: pd.DataFrame):
    """
    Creates an interactive scatter plot: Delta SR vs Pressure Balls faced.
    """
    df = all_batters.copy()
    top_ids = set(top10_batters['striker_id'])
    df['is_top10'] = df['striker_id'].isin(top_ids)
    df['group'] = df['is_top10'].map({True: 'Top 10 PPI Performer', False: 'Other Eligible Batters'})
    
    fig = px.scatter(
        df,
        x='hp_balls',
        y='delta_sr',
        size='ppi_score',
        color='group',
        hover_name='striker_name',
        hover_data={
            'ppi_score': ':.2f',
            'hp_sr': ':.1f',
            'base_sr': ':.1f',
            'rvae_per_ball': ':.3f',
            'group': False
        },
        color_discrete_map={
            'Top 10 PPI Performer': RR_PINK_LIGHT,
            'Other Eligible Batters': '#64748B'
        },
        labels={
            'hp_balls': 'High-Pressure Balls Faced',
            'delta_sr': 'Δ Strike Rate (Pressure SR − Baseline SR)',
            'ppi_score': 'PPI Score'
        },
        title="Batter Acceleration: Δ Strike Rate vs Sample Size (Bubble Size = PPI Score)"
    )
    
    # Add horizontal baseline line (delta = 0)
    fig.add_hline(y=0, line_dash="dash", line_color="#94A3B8", annotation_text="Baseline Par (Δ SR = 0)", annotation_position="bottom right")
    
    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor=RR_NAVY_CARD,
        plot_bgcolor=RR_NAVY_CARD,
        font=dict(color=RR_WHITE, family="Segoe UI, sans-serif"),
        height=520,
        margin=dict(l=20, r=20, t=50, b=30),
        xaxis=dict(showgrid=True, gridcolor="#223048"),
        yaxis=dict(showgrid=True, gridcolor="#223048"),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
            bgcolor="rgba(21, 30, 51, 0.8)"
        )
    )
    
    return fig


def create_bowler_scatter_chart(all_bowlers: pd.DataFrame, top10_bowlers: pd.DataFrame):
    """
    Creates an interactive scatter plot: Delta Economy vs RSAE/ball.
    """
    df = all_bowlers.copy()
    top_ids = set(top10_bowlers['bowler_id'])
    df['is_top10'] = df['bowler_id'].isin(top_ids)
    df['group'] = df['is_top10'].map({True: 'Top 10 PPI Performer', False: 'Other Eligible Bowlers'})
    
    fig = px.scatter(
        df,
        x='rsae_per_ball',
        y='delta_econ',
        size='ppi_score',
        color='group',
        hover_name='bowler_name',
        hover_data={
            'ppi_score': ':.2f',
            'hp_econ': ':.2f',
            'base_econ': ':.2f',
            'hp_dot_pct': ':.1f',
            'group': False
        },
        color_discrete_map={
            'Top 10 PPI Performer': RR_BLUE_LIGHT,
            'Other Eligible Bowlers': '#64748B'
        },
        labels={
            'rsae_per_ball': 'Runs Saved Above Expected / Ball (RSAE)',
            'delta_econ': 'Δ Economy Rate (Pressure Econ − Baseline Econ)',
            'ppi_score': 'PPI Score'
        },
        title="Bowler Containment: Δ Economy vs RSAE/ball (Bubble Size = PPI Score)"
    )
    
    fig.add_hline(y=0, line_dash="dash", line_color="#94A3B8", annotation_text="Baseline Par (Δ Econ = 0)", annotation_position="top right")
    fig.add_vline(x=0, line_dash="dash", line_color="#94A3B8")
    
    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor=RR_NAVY_CARD,
        plot_bgcolor=RR_NAVY_CARD,
        font=dict(color=RR_WHITE, family="Segoe UI, sans-serif"),
        height=520,
        margin=dict(l=20, r=20, t=50, b=30),
        xaxis=dict(showgrid=True, gridcolor="#223048"),
        yaxis=dict(showgrid=True, gridcolor="#223048"),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
            bgcolor="rgba(21, 30, 51, 0.8)"
        )
    )
    
    return fig


def create_player_radar_chart(player_row: pd.Series, is_batter: bool = True, benchmark_df: pd.DataFrame = None):
    """
    Renders an interactive radar chart comparing a player's percentile rankings across 5 key metrics.
    """
    if is_batter:
        categories = ['RVAE / Ball', 'Pressure SR', 'Δ Strike Rate', 'Dot Avoidance %', 'Consistency']
        
        # Calculate percentiles relative to all eligible batters
        vals = [
            (benchmark_df['rvae_per_ball'] <= player_row['rvae_per_ball']).mean() * 100 if benchmark_df is not None else 85,
            (benchmark_df['hp_sr'] <= player_row['hp_sr']).mean() * 100 if benchmark_df is not None else 80,
            (benchmark_df['delta_sr'] <= player_row['delta_sr']).mean() * 100 if benchmark_df is not None else 75,
            (benchmark_df['hp_dot_avoid'] <= player_row['hp_dot_avoid']).mean() * 100 if benchmark_df is not None else 80,
            (benchmark_df['consistency'] <= player_row['consistency']).mean() * 100 if benchmark_df is not None else 85
        ]
        color = RR_PINK
        fill_color = "rgba(217, 30, 91, 0.35)"
        name = player_row['striker_name']
    else:
        categories = ['RSAE / Ball', 'Econ Suppression', 'Dot Ball %', 'Wicket Threat', 'Consistency']
        vals = [
            (benchmark_df['rsae_per_ball'] <= player_row['rsae_per_ball']).mean() * 100 if benchmark_df is not None else 85,
            (benchmark_df['delta_econ'] >= player_row['delta_econ']).mean() * 100 if benchmark_df is not None else 80, # lower econ is better
            (benchmark_df['hp_dot_pct'] <= player_row['hp_dot_pct']).mean() * 100 if benchmark_df is not None else 80,
            (benchmark_df['hp_wkt_rate'] <= player_row['hp_wkt_rate']).mean() * 100 if benchmark_df is not None else 75,
            (benchmark_df['consistency'] <= player_row['consistency']).mean() * 100 if benchmark_df is not None else 85
        ]
        color = RR_BLUE
        fill_color = "rgba(30, 136, 229, 0.35)"
        name = player_row['bowler_name']
        
    fig = go.Figure()

    # Median Benchmark
    fig.add_trace(go.Scatterpolar(
        r=[50, 50, 50, 50, 50, 50],
        theta=categories + [categories[0]],
        fill='toself',
        fillcolor="rgba(100, 116, 139, 0.15)",
        line=dict(color="#64748B", dash="dash"),
        name="Tournament Median (50th %ile)"
    ))

    # Player Polygon
    fig.add_trace(go.Scatterpolar(
        r=vals + [vals[0]],
        theta=categories + [categories[0]],
        fill='toself',
        fillcolor=fill_color,
        line=dict(color=color, width=2.5),
        name=f"{name} (Percentiles)"
    ))

    fig.update_layout(
        template="plotly_dark",
        polar=dict(
            radialaxis=dict(visible=True, range=[0, 100], showticklabels=True, tickfont=dict(size=10, color="#94A3B8")),
            bgcolor=RR_NAVY_CARD
        ),
        paper_bgcolor=RR_NAVY_CARD,
        plot_bgcolor=RR_NAVY_CARD,
        font=dict(color=RR_WHITE, family="Segoe UI, sans-serif"),
        height=380,
        margin=dict(l=35, r=35, t=30, b=30),
        legend=dict(orientation="h", yanchor="bottom", y=-0.15, xanchor="center", x=0.5)
    )

    return fig


def create_sensitivity_plot(sens_df: pd.DataFrame, category: str = "Batter"):
    """
    Renders an interactive sensitivity line chart across pressure thresholds 60, 65, and 70.
    """
    df = sens_df[sens_df['category'] == category].copy()
    
    # Pick Top 6 players from threshold 65 to track
    ref_players = df[df['threshold'] == 65].sort_values('rank').head(6)['player_name'].tolist()
    sub_df = df[df['player_name'].isin(ref_players)].copy()
    
    fig = px.line(
        sub_df,
        x='threshold',
        y='rank',
        color='player_name',
        markers=True,
        title=f"Threshold Sensitivity (60 vs 65 vs 70) — Top {category}s Rank Stability",
        labels={'threshold': 'High-Pressure Threshold Cutoff', 'rank': 'Rank Position', 'player_name': 'Player'},
        color_discrete_sequence=px.colors.qualitative.Plotly
    )
    
    fig.update_yaxes(autorange="reversed", dtick=1)
    fig.update_xaxes(tickvals=[60, 65, 70])
    
    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor=RR_NAVY_CARD,
        plot_bgcolor=RR_NAVY_CARD,
        font=dict(color=RR_WHITE, family="Segoe UI, sans-serif"),
        height=400,
        margin=dict(l=20, r=20, t=50, b=30),
        xaxis=dict(showgrid=True, gridcolor="#223048"),
        yaxis=dict(showgrid=True, gridcolor="#223048"),
        legend=dict(bgcolor="rgba(21, 30, 51, 0.8)")
    )
    
    return fig
