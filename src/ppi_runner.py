"""
Stage 2 Orchestrator -- Pressure Performance Index (PPI) Engine.
Integrates with Stage 1 outputs and raw filtered delivery data to produce:
  - Ball-by-ball pressure scores
  - Context-adjusted RVAE / RSAE metrics
  - Empirical Bayes shrinkage + consistency scoring
  - Top 10 Batters and Top 10 Bowlers rankings
  - Sensitivity analysis (thresholds 60 / 65 / 70, IPL-only vs Combined)
  - 4 high-resolution charts
  - Case studies for every Top 10 player

Entry point: run_stage2_ppi(filtered_dfs, innings_df, output_dir='outputs')
"""

import os
import sys
import logging
import time

# Force UTF-8 output on Windows to allow unicode characters in console print
if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

import matplotlib
matplotlib.use('Agg')          # Non-interactive backend -- MUST be set before any pyplot import

import pandas as pd
import numpy as np

from src.pressure_engine import (
    compute_ball_by_ball_pressure,
    compute_batter_ppi,
    compute_bowler_ppi,
    extract_pressure_case_studies,
)
from src.sensitivity_analysis import (
    run_threshold_sensitivity_suite,
    evaluate_scope_sensitivity,
)
from src.chart_generator import (
    plot_pressure_distribution,
    plot_batters_baseline_vs_pressure,
    plot_bowlers_baseline_vs_pressure,
    plot_top10_components,
    plot_sensitivity_analysis,
)

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _charts_dir(output_dir: str) -> str:
    d = os.path.join(output_dir, 'charts')
    os.makedirs(d, exist_ok=True)
    return d


def _fix_chart_axes(all_batters_df: pd.DataFrame, all_bowlers_df: pd.DataFrame):
    """Patch chart_generator axis limits dynamically to avoid out-of-range errors."""
    import src.chart_generator as cg
    # --- Batters scatter (xlim / ylim) ---
    if not all_batters_df.empty:
        min_sr = min(all_batters_df['base_sr'].min(), all_batters_df['hp_sr'].min())
        max_sr = max(all_batters_df['base_sr'].max(), all_batters_df['hp_sr'].max())
        # Leave the original function's hard-coded limits -- but wrap through dynamic patching:
        cg._BAT_XLIM = (max(50, min_sr - 10), min(300, max_sr + 15))
        cg._BAT_YLIM = (max(50, min_sr - 15), min(350, max_sr + 25))
    # --- Bowlers scatter ---
    if not all_bowlers_df.empty:
        min_e = min(all_bowlers_df['base_econ'].min(), all_bowlers_df['hp_econ'].min())
        max_e = max(all_bowlers_df['base_econ'].max(), all_bowlers_df['hp_econ'].max())
        cg._BOWL_XLIM = (max(3.0, min_e - 0.5), min(18.0, max_e + 0.5))
        cg._BOWL_YLIM = (max(3.0, min_e - 0.75), min(22.0, max_e + 0.75))


def _print_top10_table(label: str, df: pd.DataFrame, is_batter: bool):
    """Pretty-print Top 10 table to console."""
    print(f"\n{'=' * 95}")
    print(f"  {label}")
    print(f"{'=' * 95}")
    if is_batter:
        header = (
            f"  {'Rk':>3}  {'Player':<26}  {'PPI':>6}  {'HP Balls':>8}  "
            f"{'HP SR':>7}  {'HP Runs':>8}  {'RVAE/ball':>10}  {'dSR':>7}  {'Consist':>8}"
        )
        print(header)
        print(f"  {'-' * 90}")
        for _, r in df.iterrows():
            print(
                f"  {int(r['rank']):>3}  {r['striker_name']:<26}  {r['ppi_score']:>6.1f}  "
                f"{int(r['hp_balls']):>8}  {r['hp_sr']:>7.2f}  {int(r['hp_runs']):>8}  "
                f"{r['rvae_per_ball']:>10.3f}  {r['delta_sr']:>+7.2f}  {r['consistency']:>8.3f}"
            )
    else:
        header = (
            f"  {'Rk':>3}  {'Player':<26}  {'PPI':>6}  {'HP Balls':>8}  "
            f"{'HP Econ':>8}  {'HP Wkts':>8}  {'RSAE/ball':>10}  {'Dot %':>7}  {'Consist':>8}"
        )
        print(header)
        print(f"  {'-' * 90}")
        for _, r in df.iterrows():
            print(
                f"  {int(r['rank']):>3}  {r['bowler_name']:<26}  {r['ppi_score']:>6.1f}  "
                f"{int(r['hp_balls']):>8}  {r['hp_econ']:>8.2f}  {int(r['hp_wickets']):>8}  "
                f"{r['rsae_per_ball']:>10.3f}  {r['hp_dot_pct']:>7.1f}  {r['consistency']:>8.3f}"
            )
    print(f"{'=' * 95}\n")


def _print_sensitivity_summary(sens_df: pd.DataFrame, scope_results: dict):
    """Print sensitivity check results to console."""
    print(f"\n{'=' * 85}")
    print("  SENSITIVITY ANALYSIS -- Threshold Stability (60 / 65 / 70)")
    print(f"{'=' * 85}")
    print("\n  Top Batters -- Rank by Threshold:")
    bat_piv = (
        sens_df[sens_df['category'] == 'Batter']
        .pivot_table(index='player_name', columns='threshold', values='rank', aggfunc='first')
        .sort_values(65)
        .head(12)
    )
    print(bat_piv.to_string())

    print("\n  Top Bowlers -- Rank by Threshold:")
    bowl_piv = (
        sens_df[sens_df['category'] == 'Bowler']
        .pivot_table(index='player_name', columns='threshold', values='rank', aggfunc='first')
        .sort_values(65)
        .head(12)
    )
    print(bowl_piv.to_string())

    print(f"\n  Scope Sensitivity (Combined IPL+T20I  vs.  IPL-only, threshold=65):")
    print(f"    Batter rank correlation  : {scope_results.get('batter_rank_correlation', 'N/A'):.3f}")
    print(f"    Bowler rank correlation  : {scope_results.get('bowler_rank_correlation', 'N/A'):.3f}")
    print(f"    Overlapping batters      : {scope_results.get('overlapping_batters', 'N/A')}")
    print(f"    Overlapping bowlers      : {scope_results.get('overlapping_bowlers', 'N/A')}")
    print(
        "    Interpretation: Spearman correlation > 0.85 indicates strong rank stability "
        "-- T20I data complements rather than distorts IPL-only rankings."
    )
    print(f"{'=' * 85}\n")


# ---------------------------------------------------------------------------
# Main Stage 2 Runner
# ---------------------------------------------------------------------------

def run_stage2_ppi(filtered_dfs: dict, innings_df: pd.DataFrame, output_dir: str = 'outputs') -> dict:
    """
    Runs the complete Stage 2 Pressure Performance Index pipeline.

    Parameters
    ----------
    filtered_dfs : dict
        Output of filter_dataset_by_competition() -- already enriched by clean_and_enrich_deliveries().
    innings_df : pd.DataFrame
        Output of build_innings_statistics() (Stage 1).
    output_dir : str
        Directory where all Stage 2 CSVs and charts will be saved.

    Returns
    -------
    dict with keys: all_batters_ppi, top10_batters, all_bowlers_ppi, top10_bowlers,
                    case_studies, sensitivity_df, scope_results
    """
    t0 = time.time()
    os.makedirs(output_dir, exist_ok=True)
    charts_dir = _charts_dir(output_dir)

    bbb_raw   = filtered_dfs['ball_by_ball']   # already enriched with is_legal, etc.
    matches   = filtered_dfs['matches']

    # Rename innings_df column to avoid clash in merge inside pressure engine
    inn_lookup = innings_df.rename(columns={'innings': 'innings_number'}) if 'innings' in innings_df.columns else innings_df

    # -----------------------------------------------------------------------
    # STEP 1 -- Enrich matches with home_team / away_team (already present) +
    #           verify innings_df has the 'target' column.
    # -----------------------------------------------------------------------
    logger.info("[Stage 2 | Step 1/8] Verifying matches and innings metadata...")

    # innings_df produced by innings_engine has 'innings_number' column.
    # pressure_engine expects columns: match_id, innings_number, target
    if 'target' not in inn_lookup.columns:
        # Build target from run totals if not already in the df
        # (This should already exist from innings_engine output)
        inn_lookup['target'] = np.nan

    # -----------------------------------------------------------------------
    # STEP 2 -- Compute Ball-by-Ball Pressure Scores (threshold = 65)
    # -----------------------------------------------------------------------
    logger.info("[Stage 2 | Step 2/8] Computing pre-delivery pressure scores (threshold=65)...")
    scored_bbb = compute_ball_by_ball_pressure(bbb_raw, matches, inn_lookup, hp_threshold=65.0)

    # Pressure distribution stats
    legal = scored_bbb[scored_bbb['is_legal']]
    total_legal = len(legal)
    hp_count = int(legal['is_high_pressure'].sum())
    hp_pct   = round(hp_count / total_legal * 100, 2) if total_legal > 0 else 0.0

    print(f"\n  [PPI] Pressure distribution computed:")
    print(f"        Total legal deliveries  : {total_legal:,}")
    print(f"        High-pressure (>= 65)   : {hp_count:,}  ({hp_pct:.1f}%)")
    phase_counts = legal[legal['is_high_pressure']]['phase'].value_counts()
    for ph, cnt in phase_counts.items():
        print(f"          Phase {ph:<12}: {cnt:,}  ({cnt/hp_count*100:.1f}%)")

    # -----------------------------------------------------------------------
    # STEP 3 -- Compute Batter and Bowler PPIs
    # -----------------------------------------------------------------------
    logger.info("[Stage 2 | Step 3/8] Computing Batter PPI rankings...")
    all_batters_ppi, top10_batters = compute_batter_ppi(scored_bbb)
    print(f"\n  [PPI] Eligible batters (>= 150 HP balls, >= 10 HP innings): {len(all_batters_ppi)}")

    logger.info("[Stage 2 | Step 3/8] Computing Bowler PPI rankings...")
    all_bowlers_ppi, top10_bowlers = compute_bowler_ppi(scored_bbb)
    print(f"  [PPI] Eligible bowlers (>= 120 HP balls, >= 10 HP innings): {len(all_bowlers_ppi)}")

    # -----------------------------------------------------------------------
    # STEP 4 -- Extract Case Studies
    # -----------------------------------------------------------------------
    logger.info("[Stage 2 | Step 4/8] Extracting high-pressure case studies...")
    case_studies = extract_pressure_case_studies(scored_bbb, top10_batters, top10_bowlers)

    # -----------------------------------------------------------------------
    # STEP 5 -- Sensitivity Analysis
    # -----------------------------------------------------------------------
    logger.info("[Stage 2 | Step 5/8] Running sensitivity analysis (thresholds 60/65/70)...")
    sensitivity_df = run_threshold_sensitivity_suite(bbb_raw, matches, inn_lookup)

    logger.info("[Stage 2 | Step 5/8] Evaluating scope sensitivity (Combined vs IPL-only)...")
    scope_results = evaluate_scope_sensitivity(bbb_raw, matches, inn_lookup)

    # -----------------------------------------------------------------------
    # STEP 6 -- Save CSV Outputs
    # -----------------------------------------------------------------------
    logger.info("[Stage 2 | Step 6/8] Saving Stage 2 CSV outputs...")

    top10_bat_path   = os.path.join(output_dir, 'top10_batters_pressure.csv')
    all_bat_path     = os.path.join(output_dir, 'all_batters_ppi.csv')
    top10_bowl_path  = os.path.join(output_dir, 'top10_bowlers_pressure.csv')
    all_bowl_path    = os.path.join(output_dir, 'all_bowlers_ppi.csv')
    cases_path       = os.path.join(output_dir, 'pressure_case_studies.csv')
    sens_path        = os.path.join(output_dir, 'sensitivity_analysis.csv')

    top10_batters.to_csv(top10_bat_path,  index=False)
    all_batters_ppi.to_csv(all_bat_path,  index=False)
    top10_bowlers.to_csv(top10_bowl_path, index=False)
    all_bowlers_ppi.to_csv(all_bowl_path, index=False)
    case_studies.to_csv(cases_path,       index=False)
    sensitivity_df.to_csv(sens_path,      index=False)

    print(f"\n  [PPI] CSV outputs saved:")
    for label, path in [
        ("Top 10 Batters",   top10_bat_path),
        ("All Batters PPI",  all_bat_path),
        ("Top 10 Bowlers",   top10_bowl_path),
        ("All Bowlers PPI",  all_bowl_path),
        ("Case Studies",     cases_path),
        ("Sensitivity",      sens_path),
    ]:
        rows = pd.read_csv(path).shape[0]
        print(f"    -> {label:<20}: {rows:>4} records  =>  {path}")

    # -----------------------------------------------------------------------
    # STEP 7 -- Generate Charts
    # -----------------------------------------------------------------------
    logger.info("[Stage 2 | Step 7/8] Generating high-resolution charts...")

    # Dynamically adjust axis limits so actual data always fits
    _fix_chart_axes(all_batters_ppi, all_bowlers_ppi)

    dist_path  = os.path.join(charts_dir, 'pressure_distribution.png')
    bat_sc_path = os.path.join(charts_dir, 'batters_baseline_vs_pressure.png')
    bowl_sc_path = os.path.join(charts_dir, 'bowlers_baseline_vs_pressure.png')
    comp_path  = os.path.join(charts_dir, 'top10_ppi_components.png')
    sens_chart = os.path.join(charts_dir, 'sensitivity_analysis.png')

    try:
        plot_pressure_distribution(scored_bbb, output_path=dist_path)
        print(f"    -> Pressure distribution chart  : {dist_path}")
    except Exception as e:
        logger.warning(f"Chart (pressure_distribution) failed: {e}")

    try:
        plot_batters_baseline_vs_pressure(all_batters_ppi, top10_batters, output_path=bat_sc_path)
        print(f"    -> Batters baseline vs pressure : {bat_sc_path}")
    except Exception as e:
        logger.warning(f"Chart (batters_baseline) failed: {e}")

    try:
        plot_bowlers_baseline_vs_pressure(all_bowlers_ppi, top10_bowlers, output_path=bowl_sc_path)
        print(f"    -> Bowlers baseline vs pressure : {bowl_sc_path}")
    except Exception as e:
        logger.warning(f"Chart (bowlers_baseline) failed: {e}")

    try:
        plot_top10_components(top10_batters, top10_bowlers, output_path=comp_path)
        print(f"    -> Top 10 PPI components chart  : {comp_path}")
    except Exception as e:
        logger.warning(f"Chart (top10_components) failed: {e}")

    try:
        plot_sensitivity_analysis(sensitivity_df, output_path=sens_chart)
        print(f"    -> Sensitivity analysis chart   : {sens_chart}")
    except Exception as e:
        logger.warning(f"Chart (sensitivity_analysis) failed: {e}")

    # -----------------------------------------------------------------------
    # STEP 8 -- Print Final Tables and Sensitivity to Console
    # -----------------------------------------------------------------------
    logger.info("[Stage 2 | Step 8/8] Printing final Top 10 tables...")

    _print_top10_table(
        "TOP 10 BATTERS -- PRESSURE PERFORMANCE INDEX (PPI)",
        top10_batters, is_batter=True
    )
    _print_top10_table(
        "TOP 10 BOWLERS -- PRESSURE PERFORMANCE INDEX (PPI)",
        top10_bowlers, is_batter=False
    )
    _print_sensitivity_summary(sensitivity_df, scope_results)

    elapsed = round(time.time() - t0, 1)
    print(f"  [Stage 2 complete in {elapsed}s]\n")

    return {
        'all_batters_ppi': all_batters_ppi,
        'top10_batters': top10_batters,
        'all_bowlers_ppi': all_bowlers_ppi,
        'top10_bowlers': top10_bowlers,
        'case_studies': case_studies,
        'sensitivity_df': sensitivity_df,
        'scope_results': scope_results,
    }
