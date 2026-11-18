"""
Chart Generator Module for SupeRR Selector Cricket Analytics Engine.
Renders high-resolution, publication-quality visualizations for pressure distributions,
baseline comparisons, component breakdowns, and sensitivity checks with collision-free labels.
"""

import os
import logging
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

plt.rcParams['font.sans-serif'] = 'DejaVu Sans'
plt.rcParams['axes.edgecolor'] = '#CCCCCC'
plt.rcParams['axes.linewidth'] = 0.8


def plot_pressure_distribution(scored_bbb: pd.DataFrame, output_path: str = 'outputs/charts/pressure_distribution.png'):
    """
    Renders the continuous pre-delivery pressure distribution curve and highlights the >=65 threshold.
    """
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6), dpi=300)

    legal_b = scored_bbb[scored_bbb['is_legal']]
    scores = legal_b['pressure_score']

    # Subplot 1: Distribution histogram and KDE
    n, bins, patches = ax1.hist(scores, bins=50, density=True, alpha=0.65, color='#1f77b4', edgecolor='white')
    
    # Highlight high-pressure zone (>= 65)
    for patch, left_side in zip(patches, bins[:-1]):
        if left_side >= 65:
            patch.set_facecolor('#d62728')
            patch.set_alpha(0.8)

    ax1.axvline(65, color='#b2182b', linestyle='--', linewidth=2, label='High-Pressure Cutoff (Score >= 65)')
    hp_pct = (scores >= 65).mean() * 100
    ax1.text(67, ax1.get_ylim()[1] * 0.85, f'High-Pressure Zone\n{hp_pct:.1f}% of deliveries', 
             color='#b2182b', fontweight='bold', fontsize=11, bbox=dict(boxstyle='round,pad=0.3', facecolor='#ffe6e6', edgecolor='#b2182b'))

    ax1.set_title('Ball-by-Ball Pre-Delivery Situational Pressure Distribution', fontsize=12, fontweight='bold', pad=12)
    ax1.set_xlabel('Pressure Score (0 to 100)', fontsize=11)
    ax1.set_ylabel('Probability Density', fontsize=11)
    ax1.grid(True, linestyle=':', alpha=0.6)
    ax1.legend(loc='upper left', frameon=True)

    # Subplot 2: Breakdown by Innings and Phase
    hp_deliveries = legal_b[legal_b['pressure_score'] >= 65]
    phase_order = ['Powerplay', 'Middle', 'Death']
    inn1_phase = hp_deliveries[hp_deliveries['innings'] == 1]['phase'].value_counts().reindex(phase_order, fill_value=0)
    inn2_phase = hp_deliveries[hp_deliveries['innings'] == 2]['phase'].value_counts().reindex(phase_order, fill_value=0)

    x = np.arange(len(phase_order))
    width = 0.35

    ax2.bar(x - width/2, inn1_phase, width, label='Innings 1 (Collapse & Death Accel)', color='#2ca02c', alpha=0.85)
    ax2.bar(x + width/2, inn2_phase, width, label='Innings 2 (RRR & Chase Pressure)', color='#ff7f0e', alpha=0.85)

    ax2.set_title('High-Pressure Deliveries (>= 65) by Match Phase & Innings', fontsize=12, fontweight='bold', pad=12)
    ax2.set_xlabel('Match Phase', fontsize=11)
    ax2.set_ylabel('High-Pressure Delivery Count', fontsize=11)
    ax2.set_xticks(x)
    ax2.set_xticklabels(phase_order, fontsize=10, fontweight='bold')
    ax2.yaxis.set_major_formatter(ticker.StrMethodFormatter('{x:,.0f}'))
    ax2.grid(True, linestyle=':', alpha=0.6)
    ax2.legend(frameon=True)

    plt.tight_layout()
    plt.savefig(output_path, dpi=300)
    plt.close()
    logger.info(f"Saved pressure distribution chart to: {output_path}")


def plot_batters_baseline_vs_pressure(all_batters_df: pd.DataFrame, top10_batters: pd.DataFrame, output_path: str = 'outputs/charts/batters_baseline_vs_pressure.png'):
    """
    Scatter plot comparing Baseline Strike Rate vs Pressure Strike Rate with collision-free Top 10 callouts.
    """
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    fig, ax = plt.subplots(figsize=(12, 8.5), dpi=300)

    df = all_batters_df.copy()
    top_ids = set(top10_batters['striker_id'])

    rest = df[~df['striker_id'].isin(top_ids)]
    top = df[df['striker_id'].isin(top_ids)]

    ax.scatter(rest['base_sr'], rest['hp_sr'], s=rest['hp_balls'] * 0.5, alpha=0.35, color='#888888', edgecolors='black', linewidth=0.5, label='Other Eligible Batters')
    scatter_top = ax.scatter(top['base_sr'], top['hp_sr'], s=top['hp_balls'] * 0.7, c=top['ppi_score'], cmap='viridis', edgecolors='black', linewidth=1.5, zorder=5, label='Top 10 Pressure Batters')

    min_sr, max_sr = 110, 215
    ax.plot([min_sr, max_sr], [min_sr, max_sr], 'r--', alpha=0.6, label='Equal Rate (Pressure = Baseline)')

    batter_offsets = {
        1: (1.5, 7.0, 'left', 'bottom'),      # Naman Dhir
        2: (-12.0, 11.0, 'center', 'bottom'),  # Jos Buttler
        3: (-16.0, 6.0, 'right', 'bottom'),   # Shubman Gill
        4: (4.0, -6.0, 'left', 'top'),        # Suryakumar Yadav
        5: (3.0, 5.0, 'left', 'bottom'),      # Tim David
        6: (-15.0, 1.0, 'right', 'center'),   # Rishabh Pant
        7: (3.5, 7.0, 'left', 'bottom'),      # Shashank Singh
        8: (-4.0, 16.0, 'center', 'bottom'),  # Donovan Ferreira
        9: (-12.0, -8.0, 'right', 'top'),     # Sai Sudharsan
        10: (3.0, -10.0, 'left', 'top'),      # Dhruv Jurel
    }

    for _, row in top10_batters.iterrows():
        rk = int(row['rank'])
        dx, dy, ha, va = batter_offsets.get(rk, (2.0, 2.0, 'left', 'bottom'))
        ax.annotate(
            f"#{rk} {row['striker_name']}\n(PPI: {row['ppi_score']:.1f})",
            xy=(row['base_sr'], row['hp_sr']),
            xytext=(row['base_sr'] + dx, row['hp_sr'] + dy),
            fontsize=8.5,
            fontweight='bold',
            ha=ha,
            va=va,
            bbox=dict(boxstyle='round,pad=0.25', facecolor='#ffffff', alpha=0.92, edgecolor='#333333', linewidth=0.8),
            arrowprops=dict(arrowstyle='->', color='#222222', lw=0.9, shrinkA=2, shrinkB=4)
        )

    ax.set_title('Batting Reliability Under Pressure: Baseline vs. High-Pressure Strike Rate', fontsize=13, fontweight='bold', pad=15)
    ax.set_xlabel('Career Baseline Strike Rate (All Deliveries)', fontsize=11, labelpad=8)
    ax.set_ylabel('High-Pressure Strike Rate (Pressure Score >= 65)', fontsize=11, labelpad=8)
    ax.set_xlim(115, 195)
    ax.set_ylim(110, 222)
    ax.grid(True, linestyle=':', alpha=0.5)

    cbar = plt.colorbar(scatter_top, ax=ax, pad=0.02)
    cbar.set_label('Pressure Performance Index (PPI)', fontsize=10, labelpad=8)

    ax.legend(loc='lower right', frameon=True, framealpha=0.9, edgecolor='#CCCCCC')
    plt.tight_layout()
    plt.savefig(output_path, dpi=300)
    plt.close()
    logger.info(f"Saved batters baseline vs pressure chart to: {output_path}")


def plot_bowlers_baseline_vs_pressure(all_bowlers_df: pd.DataFrame, top10_bowlers: pd.DataFrame, output_path: str = 'outputs/charts/bowlers_baseline_vs_pressure.png'):
    """
    Scatter plot comparing Baseline Economy vs Pressure Economy with collision-free Top 10 callouts.
    """
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    fig, ax = plt.subplots(figsize=(12, 8.5), dpi=300)

    df = all_bowlers_df.copy()
    top_ids = set(top10_bowlers['bowler_id'])

    rest = df[~df['bowler_id'].isin(top_ids)]
    top = df[df['bowler_id'].isin(top_ids)]

    ax.scatter(rest['base_econ'], rest['hp_econ'], s=rest['hp_balls'] * 0.5, alpha=0.35, color='#888888', edgecolors='black', linewidth=0.5, label='Other Eligible Bowlers')
    scatter_top = ax.scatter(top['base_econ'], top['hp_econ'], s=top['hp_balls'] * 0.7, c=top['ppi_score'], cmap='plasma', edgecolors='black', linewidth=1.5, zorder=5, label='Top 10 Pressure Bowlers')

    min_econ, max_econ = 4.5, 11.5
    ax.plot([min_econ, max_econ], [min_econ, max_econ], 'r--', alpha=0.6, label='Equal Economy (Pressure = Baseline)')

    bowler_offsets = {
        1: (-0.75, -0.45, 'right', 'top'),     # Abrar Ahmed
        2: (0.45, -0.40, 'left', 'top'),       # Akeal Hosein
        3: (-0.15, -0.65, 'center', 'top'),    # Mohammad Nawaz
        4: (-0.75, 0.35, 'right', 'bottom'),   # Sufiyan Muqeem
        5: (-0.65, -0.30, 'right', 'top'),     # Sunil Narine
        6: (-0.75, 0.40, 'right', 'bottom'),   # Jasprit Bumrah
        7: (0.55, -0.35, 'left', 'top'),       # Hasan Mahmud
        8: (0.50, -0.30, 'left', 'top'),       # Shaheen Afridi
        9: (0.45, 0.45, 'left', 'bottom'),     # Matheesha Pathirana
        10: (0.40, 0.15, 'left', 'center'),    # Mitchell Santner
    }

    for _, row in top10_bowlers.iterrows():
        rk = int(row['rank'])
        dx, dy, ha, va = bowler_offsets.get(rk, (0.2, 0.2, 'left', 'bottom'))
        ax.annotate(
            f"#{rk} {row['bowler_name']}\n(PPI: {row['ppi_score']:.1f})",
            xy=(row['base_econ'], row['hp_econ']),
            xytext=(row['base_econ'] + dx, row['hp_econ'] + dy),
            fontsize=8.5,
            fontweight='bold',
            ha=ha,
            va=va,
            bbox=dict(boxstyle='round,pad=0.25', facecolor='#ffffff', alpha=0.92, edgecolor='#333333', linewidth=0.8),
            arrowprops=dict(arrowstyle='->', color='#222222', lw=0.9, shrinkA=2, shrinkB=4)
        )

    ax.set_title('Bowling Reliability Under Pressure: Baseline vs. High-Pressure Economy', fontsize=13, fontweight='bold', pad=15)
    ax.set_xlabel('Career Baseline Economy (All Deliveries)', fontsize=11, labelpad=8)
    ax.set_ylabel('High-Pressure Economy (Pressure Score >= 65)', fontsize=11, labelpad=8)
    ax.set_xlim(4.8, 10.5)
    ax.set_ylim(4.2, 12.0)
    ax.grid(True, linestyle=':', alpha=0.5)

    cbar = plt.colorbar(scatter_top, ax=ax, pad=0.02)
    cbar.set_label('Pressure Performance Index (PPI)', fontsize=10, labelpad=8)

    ax.legend(loc='upper left', frameon=True, framealpha=0.9, edgecolor='#CCCCCC')
    plt.tight_layout()
    plt.savefig(output_path, dpi=300)
    plt.close()
    logger.info(f"Saved bowlers baseline vs pressure chart to: {output_path}")


def plot_top10_components(top10_batters: pd.DataFrame, top10_bowlers: pd.DataFrame, output_path: str = 'outputs/charts/top10_ppi_components.png'):
    """
    Renders grouped horizontal bar chart displaying component breakdown for Top 10 Batters and Bowlers.
    """
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 7), dpi=300)

    # Batters Component breakdown
    b_df = top10_batters.sort_values('rank', ascending=False)
    y_b = np.arange(len(b_df))

    ax1.barh(y_b, b_df['ppi_score'], color='#1f77b4', alpha=0.85, edgecolor='black', height=0.6)
    for idx, row in enumerate(b_df.itertuples()):
        ax1.text(row.ppi_score + 1.0, idx, f"{row.ppi_score:.1f} (SR: {row.hp_sr:.1f}, RVAE: +{row.rvae_per_ball:.2f})", 
                 va='center', fontsize=8.5, fontweight='bold', color='#111111')

    ax1.set_yticks(y_b)
    ax1.set_yticklabels([f"#{r.rank} {r.striker_name}" for r in b_df.itertuples()], fontsize=9.5, fontweight='bold')
    ax1.set_xlim(0, 118)
    ax1.set_xlabel('Composite Pressure Performance Index (PPI)', fontsize=10)
    ax1.set_title('Top 10 Batters Under Pressure: PPI Breakdown', fontsize=11, fontweight='bold', pad=10)
    ax1.grid(True, linestyle=':', alpha=0.5, axis='x')

    # Bowlers Component breakdown
    bw_df = top10_bowlers.sort_values('rank', ascending=False)
    y_bw = np.arange(len(bw_df))

    ax2.barh(y_bw, bw_df['ppi_score'], color='#2ca02c', alpha=0.85, edgecolor='black', height=0.6)
    for idx, row in enumerate(bw_df.itertuples()):
        ax2.text(row.ppi_score + 1.0, idx, f"{row.ppi_score:.1f} (Econ: {row.hp_econ:.2f}, RSAE: +{row.rsae_per_ball:.2f})", 
                 va='center', fontsize=8.5, fontweight='bold', color='#111111')

    ax2.set_yticks(y_bw)
    ax2.set_yticklabels([f"#{r.rank} {r.bowler_name}" for r in bw_df.itertuples()], fontsize=9.5, fontweight='bold')
    ax2.set_xlim(0, 118)
    ax2.set_xlabel('Composite Pressure Performance Index (PPI)', fontsize=10)
    ax2.set_title('Top 10 Bowlers Under Pressure: PPI Breakdown', fontsize=11, fontweight='bold', pad=10)
    ax2.grid(True, linestyle=':', alpha=0.5, axis='x')

    plt.tight_layout()
    plt.savefig(output_path, dpi=300)
    plt.close()
    logger.info(f"Saved Top 10 PPI components chart to: {output_path}")


def plot_sensitivity_analysis(sensitivity_results: pd.DataFrame, output_path: str = 'outputs/charts/sensitivity_analysis.png'):
    """
    Renders rank stability across pressure thresholds (60, 65, 70) with collision-free legend placement.
    """
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6.5), dpi=300)

    thresholds = [60, 65, 70]
    markers = ['o', 's', '^', 'D', 'v', 'p', 'h']
    colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', '#8c564b', '#e377c2']

    # Subplot 1: Batters
    bat_sens = sensitivity_results[sensitivity_results['category'] == 'Batter']
    top_players = bat_sens[bat_sens['threshold'] == 65].sort_values('rank').head(7)['player_name'].tolist()

    for idx, p_name in enumerate(top_players):
        sub = bat_sens[bat_sens['player_name'] == p_name].sort_values('threshold')
        ax1.plot(sub['threshold'], sub['rank'], marker=markers[idx % len(markers)], linewidth=2.4, color=colors[idx % len(colors)], label=p_name)

    ax1.set_title('Top Batter Rank Stability Across Pressure Thresholds (60, 65, 70)', fontsize=11, fontweight='bold', pad=12)
    ax1.set_xlabel('High-Pressure Threshold Cutoff', fontsize=10, labelpad=6)
    ax1.set_ylabel('Rank Position (Lower = Better)', fontsize=10, labelpad=6)
    ax1.set_xticks(thresholds)
    ax1.set_ylim(14, 0.5)
    ax1.grid(True, linestyle=':', alpha=0.6)
    ax1.legend(loc='lower right', fontsize=8.5, frameon=True, framealpha=0.9, edgecolor='#CCCCCC')

    # Subplot 2: Bowlers
    bowl_sens = sensitivity_results[sensitivity_results['category'] == 'Bowler']
    top_bowl_players = bowl_sens[bowl_sens['threshold'] == 65].sort_values('rank').head(7)['player_name'].tolist()

    for idx, p_name in enumerate(top_bowl_players):
        sub = bowl_sens[bowl_sens['player_name'] == p_name].sort_values('threshold')
        ax2.plot(sub['threshold'], sub['rank'], marker=markers[idx % len(markers)], linewidth=2.4, color=colors[idx % len(colors)], label=p_name)

    ax2.set_title('Top Bowler Rank Stability Across Pressure Thresholds (60, 65, 70)', fontsize=11, fontweight='bold', pad=12)
    ax2.set_xlabel('High-Pressure Threshold Cutoff', fontsize=10, labelpad=6)
    ax2.set_ylabel('Rank Position (Lower = Better)', fontsize=10, labelpad=6)
    ax2.set_xticks(thresholds)
    ax2.set_ylim(14, 0.5)
    ax2.grid(True, linestyle=':', alpha=0.6)
    ax2.legend(loc='lower right', fontsize=8.5, frameon=True, framealpha=0.9, edgecolor='#CCCCCC')

    plt.tight_layout()
    plt.savefig(output_path, dpi=300)
    plt.close()
    logger.info(f"Saved sensitivity analysis chart to: {output_path}")
