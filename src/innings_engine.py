"""
Innings Engine Module for SupeRR Selector Cricket Analytics Engine.
Builds the innings-level dataset (innings_statistics.csv).
Each row represents one innings, preserving match context and calculating targets,
required runs, run rates, balls remaining, and wickets remaining.
"""

import logging
import pandas as pd
import numpy as np
from typing import Dict
from src.player_mapping import PlayerRegistry

logger = logging.getLogger(__name__)


def build_innings_statistics(filtered_dfs: Dict[str, pd.DataFrame], registry: PlayerRegistry) -> pd.DataFrame:
    """
    Computes innings-level aggregates for every played innings in eligible matches.
    """
    logger.info("Building innings_statistics...")
    bbb = filtered_dfs['ball_by_ball']
    matches = filtered_dfs['matches']

    # 1. Aggregate delivery-level records per (match_id, innings)
    inn_df = bbb.groupby(['match_id', 'innings']).agg(
        batting_team_id=('batting_team_id', 'first'),
        bowling_team_id=('bowling_team_id', 'first'),
        total_runs=('delivery_total_runs', 'sum'),
        wickets_lost=('is_wicket', 'sum'),
        legal_balls=('is_legal', 'sum')
    ).reset_index()

    # 2. Merge Match Metadata
    match_cols = [
        'match_id', 'comp_name', 'season', 'tournament_type',
        'first_inn_revised_overs', 'second_inn_revised_overs', 'revised_target'
    ]
    inn_df = pd.merge(inn_df, matches[match_cols], on='match_id', how='inner')

    # Resolve team names
    inn_df['batting_team'] = inn_df['batting_team_id'].apply(registry.get_team_name)
    inn_df['bowling_team'] = inn_df['bowling_team_id'].apply(registry.get_team_name)

    # 3. Overs and Run Rate
    inn_df['overs'] = inn_df['legal_balls'].apply(lambda b: f"{b // 6}.{b % 6}")
    overs_decimal = inn_df['legal_balls'] / 6.0
    inn_df['run_rate'] = np.where(
        overs_decimal > 0,
        (inn_df['total_runs'] / overs_decimal).round(2),
        0.0
    )

    # 4. Target and Runs Required calculation
    # Build lookup of total_runs for innings 1 and 3 by match_id
    inn1_runs_map = inn_df[inn_df['innings'] == 1].set_index('match_id')['total_runs'].to_dict()
    inn3_runs_map = inn_df[inn_df['innings'] == 3].set_index('match_id')['total_runs'].to_dict()

    def calculate_target(row):
        inn = row['innings']
        mid = row['match_id']
        rev_target = row['revised_target']
        
        if inn == 1:
            return np.nan
        elif inn == 2:
            if pd.notnull(rev_target):
                return float(rev_target)
            elif mid in inn1_runs_map:
                return float(inn1_runs_map[mid] + 1)
            else:
                return np.nan
        elif inn == 3:
            return np.nan
        elif inn == 4:
            if mid in inn3_runs_map:
                return float(inn3_runs_map[mid] + 1)
            else:
                return np.nan
        return np.nan

    inn_df['target'] = inn_df.apply(calculate_target, axis=1)

    # Runs required: applicable for chase innings (innings 2 and 4)
    def calculate_runs_required(row):
        target = row['target']
        if pd.isnull(target):
            return np.nan
        rem = target - row['total_runs']
        return max(0, int(rem))

    inn_df['runs_required'] = inn_df.apply(calculate_runs_required, axis=1)

    # 5. Balls remaining and Wickets remaining
    def calculate_balls_remaining(row):
        inn = row['innings']
        legal_b = row['legal_balls']
        
        if inn in [1, 2]:
            rev_overs = row['first_inn_revised_overs'] if inn == 1 else row['second_inn_revised_overs']
            # Note: in dataset, revised_overs is recorded in balls (e.g. 48 for 8 overs, 90 for 15 overs)
            if pd.notnull(rev_overs):
                scheduled_balls = int(rev_overs)
            else:
                scheduled_balls = 120  # Standard 20 overs
        elif inn in [3, 4]:
            scheduled_balls = 6  # Super Over
        else:
            scheduled_balls = 120
            
        return max(0, scheduled_balls - legal_b)

    def calculate_wickets_remaining(row):
        inn = row['innings']
        w_lost = row['wickets_lost']
        max_wickets = 2 if inn in [3, 4] else 10
        return max(0, max_wickets - w_lost)

    inn_df['balls_remaining'] = inn_df.apply(calculate_balls_remaining, axis=1)
    inn_df['wickets_remaining'] = inn_df.apply(calculate_wickets_remaining, axis=1)

    # Reorder columns
    inn_df = inn_df.rename(columns={
        'comp_name': 'competition',
        'innings': 'innings_number'
    })

    ordered_cols = [
        'match_id',
        'competition',
        'season',
        'innings_number',
        'batting_team',
        'bowling_team',
        'total_runs',
        'wickets_lost',
        'legal_balls',
        'overs',
        'run_rate',
        'target',
        'runs_required',
        'balls_remaining',
        'wickets_remaining'
    ]

    inn_df = inn_df[ordered_cols].sort_values(by=['match_id', 'innings_number']).reset_index(drop=True)
    logger.info(f"Successfully built innings_statistics: {len(inn_df)} innings.")
    return inn_df
