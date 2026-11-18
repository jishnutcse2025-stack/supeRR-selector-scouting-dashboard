"""
SupeRR Selector Season 2 — Dashboard Utility Functions
Premium Light-Mode Sports Analytics SaaS Design System.
Helper modules for data caching, styling, and interactive Plotly visualizations.
Uses robust Path(__file__).resolve().parent for cloud-safe relative asset loading.
"""

from pathlib import Path
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go

# =============================================================================
# PATH CONSTANTS (BULLETPROOF CLOUD & LOCAL RESOLUTION)
# =============================================================================
BASE_DIR = Path(__file__).resolve().parent
OUTPUTS_DIR = BASE_DIR / "outputs"
CHARTS_DIR = OUTPUTS_DIR / "charts"

# =============================================================================
# EXACT COLOUR SYSTEM (PREMIUM LIGHT SAAS)
# =============================================================================
BG_MAIN = "#F5F7FC"
CARD_BG = "#FFFFFF"
TEXT_PRIMARY = "#202B45"
TEXT_SECONDARY = "#697586"
PRIMARY_BLUE = "#2698DC"
ROYAL_PINK = "#E83E8C"
PURPLE = "#7950D8"
TEAL = "#16B8A6"
ORANGE = "#F5A623"
BORDER = "#E7EAF2"

@st.cache_data
def load_data(output_dir=None):
    """
    Loads all precomputed analytics engine outputs from the outputs directory.
    Uses Path(__file__).resolve().parent for reliable path resolution in cloud environments.
    """
    target_dir = Path(output_dir) if output_dir is not None else OUTPUTS_DIR
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
    
    missing_files = []
    for key, filename in files.items():
        file_path = target_dir / filename
        if file_path.exists():
            data[key] = pd.read_csv(file_path)
        else:
            missing_files.append(filename)
            data[key] = pd.DataFrame()
            
    val_path = target_dir / 'validation_report.txt'
    if val_path.exists():
        with open(val_path, 'r', encoding='utf-8', errors='ignore') as f:
            data['validation_text'] = f.read()
    else:
        missing_files.append('validation_report.txt')
        data['validation_text'] = "Validation report not found."
        
    if missing_files:
        st.warning(f"Note: Some data files were not found in {target_dir}: {', '.join(missing_files)}")
        
    return data


def apply_custom_css():
    """
    Injects custom CSS styling for a bright, colourful, premium SaaS interface.
    Fixes header contrast and provides modern card, sidebar, and typography rules.
    """
    st.markdown(f"""
    <style>
        /* Import Google Fonts (Plus Jakarta Sans & Inter) */
        @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=Inter:wght@400;500;600;700&display=swap');

        /* Global App Canvas */
        html, body, [class*="css"] {{
            font-family: 'Plus Jakarta Sans', 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
            background-color: {BG_MAIN} !important;
            color: {TEXT_PRIMARY} !important;
        }}
        
        .stApp {{
            background-color: {BG_MAIN} !important;
            color: {TEXT_PRIMARY} !important;
        }}
        
        /* Streamlit Header / Chrome Bar — Seamless White-Header Integration */
        header[data-testid="stHeader"] {{
            background-color: {BG_MAIN} !important;
            border-bottom: 1px solid {BORDER} !important;
            height: 3.5rem !important;
        }}
        header[data-testid="stHeader"] .stActionButton {{
            color: {TEXT_PRIMARY} !important;
        }}
        
        /* Main Container Padding */
        .block-container {{
            padding-top: 2rem !important;
            padding-bottom: 3.5rem !important;
            max-width: 1380px !important;
        }}
        
        /* Sidebar Styling (Elegant Crisp White) */
        section[data-testid="stSidebar"] {{
            background-color: #FFFFFF !important;
            border-right: 1px solid {BORDER} !important;
            box-shadow: 2px 0 16px rgba(32, 43, 69, 0.04) !important;
        }}
        section[data-testid="stSidebar"] div[data-testid="stVerticalBlock"] {{
            gap: 0.5rem;
        }}
        section[data-testid="stSidebar"] hr {{
            margin: 10px 0;
            border-color: {BORDER};
        }}
        
        /* Sidebar Radio Navigation Items */
        section[data-testid="stSidebar"] div[data-testid="stRadio"] > div {{
            gap: 4px;
        }}
        section[data-testid="stSidebar"] div[data-testid="stRadio"] label {{
            color: {TEXT_PRIMARY} !important;
            font-weight: 600;
            font-size: 0.90rem;
            padding: 8px 14px;
            border-radius: 9px;
            transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
            margin-bottom: 1px;
            display: flex;
            align-items: center;
            border: 1px solid transparent;
        }}
        section[data-testid="stSidebar"] div[data-testid="stRadio"] label:hover {{
            background-color: #EEF4FD;
            color: {PRIMARY_BLUE} !important;
            transform: translateX(2px);
        }}
        section[data-testid="stSidebar"] div[data-testid="stRadio"] label[data-checked="true"],
        section[data-testid="stSidebar"] div[data-testid="stRadio"] label:has(input:checked) {{
            background-color: #EEF4FD !important;
            color: {PRIMARY_BLUE} !important;
            border-color: rgba(38, 152, 220, 0.3) !important;
            font-weight: 700 !important;
        }}
        
        /* Typography */
        h1, h2, h3, h4, h5, h6 {{
            color: {TEXT_PRIMARY} !important;
            font-family: 'Plus Jakarta Sans', sans-serif !important;
            font-weight: 800;
            letter-spacing: -0.025em;
        }}
        p, span, label {{
            color: {TEXT_PRIMARY};
        }}

        /* Premium SaaS Content & KPI Cards */
        .saas-card {{
            background-color: {CARD_BG};
            border: 1px solid {BORDER};
            border-radius: 14px;
            padding: 20px 22px;
            margin-bottom: 16px;
            box-shadow: 0 4px 18px rgba(32, 43, 69, 0.04);
            transition: transform 0.2s ease, box-shadow 0.2s ease, border-color 0.2s ease;
            position: relative;
        }}
        .saas-card:hover {{
            transform: translateY(-2px);
            box-shadow: 0 10px 28px rgba(32, 43, 69, 0.08);
            border-color: #D3DBE8;
        }}
        
        /* Colourful Card Top Accents */
        .card-accent-blue {{ border-top: 4px solid {PRIMARY_BLUE}; }}
        .card-accent-pink {{ border-top: 4px solid {ROYAL_PINK}; }}
        .card-accent-purple {{ border-top: 4px solid {PURPLE}; }}
        .card-accent-teal {{ border-top: 4px solid {TEAL}; }}
        .card-accent-orange {{ border-top: 4px solid {ORANGE}; }}
        
        .kpi-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 8px;
        }}
        .kpi-title {{
            font-size: 0.76rem;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.07em;
            color: {TEXT_SECONDARY};
        }}
        .kpi-icon-wrap {{
            width: 34px;
            height: 34px;
            border-radius: 9px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 1.1rem;
        }}
        .kpi-value {{
            font-size: 2.2rem;
            font-weight: 800;
            color: {TEXT_PRIMARY};
            line-height: 1.1;
            margin-bottom: 4px;
            letter-spacing: -0.03em;
        }}
        .kpi-subtitle {{
            font-size: 0.82rem;
            color: {TEXT_SECONDARY};
            font-weight: 500;
        }}
        
        /* Badges & Status Pills */
        .badge {{
            display: inline-flex;
            align-items: center;
            border-radius: 7px;
            padding: 3px 10px;
            font-size: 0.76rem;
            font-weight: 700;
            letter-spacing: 0.02em;
        }}
        .badge-blue {{ background-color: rgba(38, 152, 220, 0.12); color: {PRIMARY_BLUE}; border: 1px solid rgba(38, 152, 220, 0.28); }}
        .badge-pink {{ background-color: rgba(232, 62, 140, 0.12); color: {ROYAL_PINK}; border: 1px solid rgba(232, 62, 140, 0.28); }}
        .badge-purple {{ background-color: rgba(121, 80, 216, 0.12); color: {PURPLE}; border: 1px solid rgba(121, 80, 216, 0.28); }}
        .badge-teal {{ background-color: rgba(22, 184, 166, 0.12); color: {TEAL}; border: 1px solid rgba(22, 184, 166, 0.28); }}
        .badge-orange {{ background-color: rgba(245, 166, 35, 0.12); color: {ORANGE}; border: 1px solid rgba(245, 166, 35, 0.28); }}
        
        /* Modern Segmented Tabs */
        .stTabs [data-baseweb="tab-list"] {{
            background-color: #EAEFF8;
            padding: 5px;
            border-radius: 11px;
            gap: 6px;
        }}
        .stTabs [data-baseweb="tab"] {{
            background-color: transparent;
            border-radius: 8px;
            padding: 8px 20px;
            color: {TEXT_SECONDARY};
            font-weight: 700;
            font-size: 0.88rem;
            border: none;
            transition: all 0.2s ease;
        }}
        .stTabs [data-baseweb="tab"]:hover {{
            color: {TEXT_PRIMARY};
            background-color: rgba(255, 255, 255, 0.5);
        }}
        .stTabs [aria-selected="true"] {{
            background-color: #FFFFFF !important;
            color: {TEXT_PRIMARY} !important;
            box-shadow: 0 3px 10px rgba(32, 43, 69, 0.08);
        }}

        /* Buttons (Vibrant SaaS Gradient) */
        .stButton>button {{
            background: linear-gradient(135deg, {PRIMARY_BLUE} 0%, #1a7ebc 100%) !important;
            color: #FFFFFF !important;
            border: none !important;
            border-radius: 9px !important;
            padding: 8px 20px !important;
            font-weight: 700 !important;
            box-shadow: 0 3px 12px rgba(38, 152, 220, 0.28) !important;
            transition: all 0.2s ease !important;
        }}
        .stButton>button:hover {{
            background: linear-gradient(135deg, #3aa7e8 0%, {PRIMARY_BLUE} 100%) !important;
            box-shadow: 0 6px 18px rgba(38, 152, 220, 0.38) !important;
            transform: translateY(-1px) !important;
        }}
        
        /* Download Buttons */
        .stDownloadButton>button {{
            background: #FFFFFF !important;
            color: {TEXT_PRIMARY} !important;
            border: 1px solid {BORDER} !important;
            border-radius: 9px !important;
            font-weight: 700 !important;
            box-shadow: 0 2px 8px rgba(32, 43, 69, 0.04) !important;
            transition: all 0.2s ease !important;
        }}
        .stDownloadButton>button:hover {{
            border-color: {PRIMARY_BLUE} !important;
            color: {PRIMARY_BLUE} !important;
            background: #F8FAFC !important;
            transform: translateY(-1px) !important;
            box-shadow: 0 4px 14px rgba(38, 152, 220, 0.15) !important;
        }}
        
        /* Table & DataFrames */
        div[data-testid="stDataFrame"] {{
            background-color: #FFFFFF !important;
            border: 1px solid {BORDER} !important;
            border-radius: 12px !important;
            overflow: hidden;
            box-shadow: 0 3px 12px rgba(32, 43, 69, 0.03);
        }}

        /* Input Elements */
        .stTextInput>div>div>input {{
            background-color: #FFFFFF !important;
            border: 1px solid {BORDER} !important;
            border-radius: 9px !important;
            color: {TEXT_PRIMARY} !important;
            font-weight: 500;
        }}
        .stTextInput>div>div>input:focus {{
            border-color: {PRIMARY_BLUE} !important;
            box-shadow: 0 0 0 2px rgba(38, 152, 220, 0.2) !important;
        }}
        .stSelectbox>div>div {{
            background-color: #FFFFFF !important;
            border: 1px solid {BORDER} !important;
            border-radius: 9px !important;
            color: {TEXT_PRIMARY} !important;
        }}
        
        /* Metric widget styling */
        div[data-testid="stMetricValue"] {{
            color: {TEXT_PRIMARY} !important;
            font-weight: 800 !important;
        }}
        div[data-testid="stMetricLabel"] {{
            color: {TEXT_SECONDARY} !important;
            font-weight: 700 !important;
        }}
    </style>
    """, unsafe_allow_html=True)


def render_metric_card(title: str, value: str, subtitle: str = "", accent: str = "blue", icon: str = "📊"):
    """
    Renders a bright, modern SaaS KPI card with a colourful accent and icon.
    """
    accent_map = {
        'blue': ('card-accent-blue', 'rgba(38, 152, 220, 0.12)', PRIMARY_BLUE),
        'pink': ('card-accent-pink', 'rgba(232, 62, 140, 0.12)', ROYAL_PINK),
        'purple': ('card-accent-purple', 'rgba(121, 80, 216, 0.12)', PURPLE),
        'teal': ('card-accent-teal', 'rgba(22, 184, 166, 0.12)', TEAL),
        'orange': ('card-accent-orange', 'rgba(245, 166, 35, 0.12)', ORANGE)
    }
    
    card_class, icon_bg, icon_color = accent_map.get(accent, ('card-accent-blue', 'rgba(38, 152, 220, 0.12)', PRIMARY_BLUE))
    
    st.markdown(f"""
    <div class="saas-card {card_class}">
        <div class="kpi-header">
            <span class="kpi-title">{title}</span>
            <div class="kpi-icon-wrap" style="background-color: {icon_bg}; color: {icon_color};">
                {icon}
            </div>
        </div>
        <div class="kpi-value">{value}</div>
        <div class="kpi-subtitle">{subtitle}</div>
    </div>
    """, unsafe_allow_html=True)


def create_top10_bar_chart(df: pd.DataFrame, is_batter: bool = True):
    """
    Creates an interactive horizontal bar chart for the Top 10 PPI performers in Light Mode.
    """
    player_col = 'striker_name' if is_batter else 'bowler_name'
    title = "Top 10 Batters — Pressure Performance Index (PPI)" if is_batter else "Top 10 Bowlers — Pressure Performance Index (PPI)"
    color_scale = [[0, '#ffd1e8'], [1, ROYAL_PINK]] if is_batter else [[0, '#c7e6fa'], [1, PRIMARY_BLUE]]
    
    plot_df = df.sort_values('ppi_score', ascending=True).copy()
    
    fig = px.bar(
        plot_df,
        x='ppi_score',
        y=player_col,
        orientation='h',
        text='ppi_score',
        title=f"<b>{title}</b>",
        color='ppi_score',
        color_continuous_scale=color_scale,
        labels={'ppi_score': 'PPI Score (40–100)', player_col: 'Player'}
    )
    
    fig.update_traces(
        texttemplate='%{text:.2f}',
        textposition='outside',
        marker=dict(line=dict(width=1, color="#FFFFFF")),
        hovertemplate="<b>%{y}</b><br>PPI Score: <b>%{x:.2f}</b><extra></extra>"
    )
    
    fig.update_layout(
        template="plotly_white",
        paper_bgcolor=CARD_BG,
        plot_bgcolor=CARD_BG,
        font=dict(color=TEXT_PRIMARY, family="Plus Jakarta Sans, sans-serif"),
        height=460,
        margin=dict(l=20, r=45, t=55, b=30),
        xaxis=dict(
            range=[35, 105], 
            showgrid=True, 
            gridcolor=BORDER,
            zeroline=False,
            tickfont=dict(color=TEXT_SECONDARY)
        ),
        yaxis=dict(
            showgrid=False,
            tickfont=dict(color=TEXT_PRIMARY, size=12)
        ),
        coloraxis_showscale=False
    )
    
    return fig


def create_batter_scatter_chart(all_batters: pd.DataFrame, top10_batters: pd.DataFrame):
    """
    Creates an interactive scatter plot: Delta SR vs Pressure Balls faced in Light Mode.
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
            'Top 10 PPI Performer': ROYAL_PINK,
            'Other Eligible Batters': '#A0AEC0'
        },
        labels={
            'hp_balls': 'High-Pressure Balls Faced',
            'delta_sr': 'Δ Strike Rate (Pressure SR − Baseline SR)',
            'ppi_score': 'PPI Score'
        },
        title="<b>Batter Acceleration: Δ Strike Rate vs Sample Size (Bubble Size = PPI Score)</b>"
    )
    
    fig.add_hline(
        y=0, 
        line_dash="dash", 
        line_color="#CBD5E1", 
        annotation_text="Baseline Par (Δ SR = 0)", 
        annotation_position="bottom right",
        annotation_font=dict(color=TEXT_SECONDARY, size=11)
    )
    
    fig.update_traces(
        marker=dict(line=dict(width=1.5, color="#FFFFFF")),
        opacity=0.88
    )
    
    fig.update_layout(
        template="plotly_white",
        paper_bgcolor=CARD_BG,
        plot_bgcolor=CARD_BG,
        font=dict(color=TEXT_PRIMARY, family="Plus Jakarta Sans, sans-serif"),
        height=520,
        margin=dict(l=20, r=20, t=55, b=30),
        xaxis=dict(showgrid=True, gridcolor=BORDER, tickfont=dict(color=TEXT_SECONDARY)),
        yaxis=dict(showgrid=True, gridcolor=BORDER, tickfont=dict(color=TEXT_SECONDARY)),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
            bgcolor="rgba(255, 255, 255, 0.95)",
            bordercolor=BORDER,
            borderwidth=1
        )
    )
    
    return fig


def create_bowler_scatter_chart(all_bowlers: pd.DataFrame, top10_bowlers: pd.DataFrame):
    """
    Creates an interactive scatter plot: Delta Economy vs RSAE/ball in Light Mode.
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
            'Top 10 PPI Performer': PRIMARY_BLUE,
            'Other Eligible Bowlers': '#A0AEC0'
        },
        labels={
            'rsae_per_ball': 'Runs Saved Above Expected / Ball (RSAE)',
            'delta_econ': 'Δ Economy Rate (Pressure Econ − Baseline Econ)',
            'ppi_score': 'PPI Score'
        },
        title="<b>Bowler Containment: Δ Economy vs RSAE/ball (Bubble Size = PPI Score)</b>"
    )
    
    fig.add_hline(
        y=0, 
        line_dash="dash", 
        line_color="#CBD5E1", 
        annotation_text="Baseline Par (Δ Econ = 0)", 
        annotation_position="top right",
        annotation_font=dict(color=TEXT_SECONDARY, size=11)
    )
    fig.add_vline(x=0, line_dash="dash", line_color="#CBD5E1")
    
    fig.update_traces(
        marker=dict(line=dict(width=1.5, color="#FFFFFF")),
        opacity=0.88
    )
    
    fig.update_layout(
        template="plotly_white",
        paper_bgcolor=CARD_BG,
        plot_bgcolor=CARD_BG,
        font=dict(color=TEXT_PRIMARY, family="Plus Jakarta Sans, sans-serif"),
        height=520,
        margin=dict(l=20, r=20, t=55, b=30),
        xaxis=dict(showgrid=True, gridcolor=BORDER, tickfont=dict(color=TEXT_SECONDARY)),
        yaxis=dict(showgrid=True, gridcolor=BORDER, tickfont=dict(color=TEXT_SECONDARY)),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
            bgcolor="rgba(255, 255, 255, 0.95)",
            bordercolor=BORDER,
            borderwidth=1
        )
    )
    
    return fig


def create_player_radar_chart(player_row: pd.Series, is_batter: bool = True, benchmark_df: pd.DataFrame = None):
    """
    Renders an interactive radar chart comparing a player's percentile rankings in Light Mode.
    """
    if is_batter:
        categories = ['RVAE / Ball', 'Pressure SR', 'Δ Strike Rate', 'Dot Avoidance %', 'Consistency']
        vals = [
            (benchmark_df['rvae_per_ball'] <= player_row['rvae_per_ball']).mean() * 100 if benchmark_df is not None else 85,
            (benchmark_df['hp_sr'] <= player_row['hp_sr']).mean() * 100 if benchmark_df is not None else 80,
            (benchmark_df['delta_sr'] <= player_row['delta_sr']).mean() * 100 if benchmark_df is not None else 75,
            (benchmark_df['hp_dot_avoid'] <= player_row['hp_dot_avoid']).mean() * 100 if benchmark_df is not None else 80,
            (benchmark_df['consistency'] <= player_row['consistency']).mean() * 100 if benchmark_df is not None else 85
        ]
        color = ROYAL_PINK
        fill_color = "rgba(232, 62, 140, 0.22)"
        name = player_row['striker_name']
    else:
        categories = ['RSAE / Ball', 'Econ Suppression', 'Dot Ball %', 'Wicket Threat', 'Consistency']
        vals = [
            (benchmark_df['rsae_per_ball'] <= player_row['rsae_per_ball']).mean() * 100 if benchmark_df is not None else 85,
            (benchmark_df['delta_econ'] >= player_row['delta_econ']).mean() * 100 if benchmark_df is not None else 80,
            (benchmark_df['hp_dot_pct'] <= player_row['hp_dot_pct']).mean() * 100 if benchmark_df is not None else 80,
            (benchmark_df['hp_wkt_rate'] <= player_row['hp_wkt_rate']).mean() * 100 if benchmark_df is not None else 75,
            (benchmark_df['consistency'] <= player_row['consistency']).mean() * 100 if benchmark_df is not None else 85
        ]
        color = PRIMARY_BLUE
        fill_color = "rgba(38, 152, 220, 0.22)"
        name = player_row['bowler_name']
        
    fig = go.Figure()

    # Median Benchmark
    fig.add_trace(go.Scatterpolar(
        r=[50, 50, 50, 50, 50, 50],
        theta=categories + [categories[0]],
        fill='toself',
        fillcolor="rgba(203, 213, 225, 0.2)",
        line=dict(color="#94A3B8", dash="dash", width=1.5),
        name="Tournament Median (50th %ile)"
    ))

    # Player Polygon
    fig.add_trace(go.Scatterpolar(
        r=vals + [vals[0]],
        theta=categories + [categories[0]],
        fill='toself',
        fillcolor=fill_color,
        line=dict(color=color, width=3),
        name=f"{name} (Percentiles)"
    ))

    fig.update_layout(
        template="plotly_white",
        polar=dict(
            radialaxis=dict(
                visible=True, 
                range=[0, 100], 
                showticklabels=True, 
                tickfont=dict(size=10, color=TEXT_SECONDARY),
                gridcolor=BORDER
            ),
            angularaxis=dict(
                gridcolor=BORDER,
                tickfont=dict(size=11, color=TEXT_PRIMARY, family="Plus Jakarta Sans, sans-serif")
            ),
            bgcolor="#FAFCFF"
        ),
        paper_bgcolor=CARD_BG,
        plot_bgcolor=CARD_BG,
        font=dict(color=TEXT_PRIMARY, family="Plus Jakarta Sans, sans-serif"),
        height=390,
        margin=dict(l=35, r=35, t=30, b=30),
        legend=dict(
            orientation="h", 
            yanchor="bottom", 
            y=-0.18, 
            xanchor="center", 
            x=0.5,
            bordercolor=BORDER,
            borderwidth=1,
            bgcolor="#FFFFFF"
        )
    )

    return fig


def create_sensitivity_plot(sens_df: pd.DataFrame, category: str = "Batter"):
    """
    Renders an interactive sensitivity line chart in Light Mode.
    """
    df = sens_df[sens_df['category'] == category].copy()
    
    ref_players = df[df['threshold'] == 65].sort_values('rank').head(6)['player_name'].tolist()
    sub_df = df[df['player_name'].isin(ref_players)].copy()
    
    fig = px.line(
        sub_df,
        x='threshold',
        y='rank',
        color='player_name',
        markers=True,
        title=f"<b>Threshold Sensitivity (60 vs 65 vs 70) — Top {category}s Rank Stability</b>",
        labels={'threshold': 'High-Pressure Threshold Cutoff', 'rank': 'Rank Position', 'player_name': 'Player'},
        color_discrete_sequence=[ROYAL_PINK, PRIMARY_BLUE, PURPLE, TEAL, ORANGE, "#E11D48"]
    )
    
    fig.update_traces(line=dict(width=2.5), marker=dict(size=8, line=dict(width=1.5, color="#FFFFFF")))
    fig.update_yaxes(autorange="reversed", dtick=1, gridcolor=BORDER, tickfont=dict(color=TEXT_SECONDARY))
    fig.update_xaxes(tickvals=[60, 65, 70], gridcolor=BORDER, tickfont=dict(color=TEXT_SECONDARY))
    
    fig.update_layout(
        template="plotly_white",
        paper_bgcolor=CARD_BG,
        plot_bgcolor=CARD_BG,
        font=dict(color=TEXT_PRIMARY, family="Plus Jakarta Sans, sans-serif"),
        height=410,
        margin=dict(l=20, r=20, t=55, b=30),
        legend=dict(
            bgcolor="rgba(255, 255, 255, 0.95)",
            bordercolor=BORDER,
            borderwidth=1
        )
    )
    
    return fig
