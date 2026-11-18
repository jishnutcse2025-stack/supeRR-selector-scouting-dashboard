"""
Sensitivity Analysis Module for SupeRR Selector Cricket Analytics Engine.
Evaluates ranking stability across:
1. Pressure thresholds: 60 vs. 65 vs. 70
2. Competition scope: IPL-only vs. Combined (IPL + T20I)
Computes Spearman rank correlations and stability metrics.
"""

import logging
import pandas as pd
import numpy as np
from scipy.stats import spearmanr
from typing import Dict, Tuple

from src.pressure_engine import compute_ball_by_ball_pressure, compute_batter_ppi, compute_bowler_ppi

logger = logging.getLogger(__name__)


def run_threshold_sensitivity_suite(
    raw_bbb: pd.DataFrame,
    matches_df: pd.DataFrame,
    innings_df: pd.DataFrame
) -> pd.DataFrame:
    """
    Computes rankings at thresholds 60, 65, and 70 to evaluate rank stability.
    """
    logger.info("Running sensitivity analysis across thresholds (60, 65, 70)...")
    results = []

    for th in [60, 65, 70]:
        scored = compute_ball_by_ball_pressure(raw_bbb, matches_df, innings_df, hp_threshold=float(th))
        all_bat, _ = compute_batter_ppi(scored)
        all_bowl, _ = compute_bowler_ppi(scored)

        for _, row in all_bat.head(15).iterrows():
            results.append({
                'category': 'Batter',
                'threshold': th,
                'player_id': row['striker_id'],
                'player_name': row['striker_name'],
                'rank': row['rank'],
                'ppi_score': row['ppi_score'],
                'metric_val': row['hp_sr']
            })

        for _, row in all_bowl.head(15).iterrows():
            results.append({
                'category': 'Bowler',
                'threshold': th,
                'player_id': row['bowler_id'],
                'player_name': row['bowler_name'],
                'rank': row['rank'],
                'ppi_score': row['ppi_score'],
                'metric_val': row['hp_econ']
            })

    sens_df = pd.DataFrame(results)
    return sens_df


def evaluate_scope_sensitivity(
    raw_bbb: pd.DataFrame,
    matches_df: pd.DataFrame,
    innings_df: pd.DataFrame
) -> Dict[str, float]:
    """
    Evaluates ranking stability between Combined (IPL + T20I) and IPL-only datasets.
    Computes Spearman rank correlation for top candidates.
    """
    logger.info("Evaluating scope sensitivity (Combined vs. IPL-only)...")
    
    # 1. Combined
    scored_comb = compute_ball_by_ball_pressure(raw_bbb, matches_df, innings_df, hp_threshold=65.0)
    all_bat_comb, _ = compute_batter_ppi(scored_comb)
    all_bowl_comb, _ = compute_bowler_ppi(scored_comb)

    # 2. IPL Only
    ipl_match_ids = set(matches_df[matches_df['tournament_type'] == 'IPL']['match_id'])
    bbb_ipl = raw_bbb[raw_bbb['match_id'].isin(ipl_match_ids)]
    matches_ipl = matches_df[matches_df['match_id'].isin(ipl_match_ids)]
    innings_ipl = innings_df[innings_df['match_id'].isin(ipl_match_ids)]

    scored_ipl = compute_ball_by_ball_pressure(bbb_ipl, matches_ipl, innings_ipl, hp_threshold=65.0)
    # Calibrated thresholds for IPL-only volume (>= 80 balls)
    all_bat_ipl, _ = compute_batter_ppi(scored_ipl, min_hp_balls=80, min_hp_inns=5)
    all_bowl_ipl, _ = compute_bowler_ppi(scored_ipl, min_hp_balls=60, min_hp_inns=5)

    # Spearman Correlation for overlapping batters
    bat_overlap = pd.merge(
        all_bat_comb[['striker_id', 'rank']].rename(columns={'rank': 'rank_comb'}),
        all_bat_ipl[['striker_id', 'rank']].rename(columns={'rank': 'rank_ipl'}),
        on='striker_id'
    )
    corr_bat, _ = spearmanr(bat_overlap['rank_comb'], bat_overlap['rank_ipl'])

    # Spearman Correlation for overlapping bowlers
    bowl_overlap = pd.merge(
        all_bowl_comb[['bowler_id', 'rank']].rename(columns={'rank': 'rank_comb'}),
        all_bowl_ipl[['bowler_id', 'rank']].rename(columns={'rank': 'rank_ipl'}),
        on='bowler_id'
    )
    corr_bowl, _ = spearmanr(bowl_overlap['rank_comb'], bowl_overlap['rank_ipl'])

    return {
        'batter_rank_correlation': round(float(corr_bat), 3),
        'bowler_rank_correlation': round(float(corr_bowl), 3),
        'overlapping_batters': len(bat_overlap),
        'overlapping_bowlers': len(bowl_overlap)
    }
