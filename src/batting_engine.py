"""
Batting Engine Module for SupeRR Selector Cricket Analytics Engine.
Calculates comprehensive, verified batting statistics across IPL, T20I, and Combined formats.
"""

import logging
import pandas as pd
import numpy as np
from typing import Dict
from src.player_mapping import PlayerRegistry

logger = logging.getLogger(__name__)


def build_batter_statistics(filtered_dfs: Dict[str, pd.DataFrame], registry: PlayerRegistry) -> pd.DataFrame:
    """
    Computes career batting statistics for every eligible batter in IPL (2022+) and T20I (2022+).
    """
    logger.info("Computing batter statistics...")
    bbb = filtered_dfs['ball_by_ball']
    p11 = filtered_dfs['playing_eleven']

    # 1. Matches played per player (from confirmed Playing XI)
    p11_played = p11[p11['is_played'] == True]
    player_matches = p11_played.groupby('player_id')['match_id'].nunique().to_dict()

    # 2. Innings batted and dismissals
    # A player batted if they were striker, non-striker, or dismissed in the innings
    strikers = bbb[['match_id', 'innings', 'striker_id']].rename(columns={'striker_id': 'player_id'}).drop_duplicates()
    non_strikers = bbb[['match_id', 'innings', 'non_striker_id']].rename(columns={'non_striker_id': 'player_id'}).drop_duplicates()
    
    # Dismissed players
    dismissed_rows = bbb[bbb['is_wicket'] == True].copy()
    # Handle single missing dismissed_player_id (Hardik Pandya Retire Out where striker_id was Hardik)
    dismissed_rows['clean_dismissed_id'] = dismissed_rows['dismissed_player_id'].fillna(dismissed_rows['striker_id']).astype('int64')
    dismissed_unique = dismissed_rows[['match_id', 'innings', 'clean_dismissed_id']].rename(columns={'clean_dismissed_id': 'player_id'}).drop_duplicates()
    dismissed_unique['is_dismissed'] = True

    # Combine all appearances at the crease
    all_batted_innings = pd.concat([strikers, non_strikers, dismissed_unique[['match_id', 'innings', 'player_id']]]).drop_duplicates()

    # Merge dismissal status per innings
    innings_status = pd.merge(all_batted_innings, dismissed_unique, on=['match_id', 'innings', 'player_id'], how='left')
    innings_status['is_dismissed'] = innings_status['is_dismissed'].astype('boolean').fillna(False).astype(bool)

    # Calculate per-player innings batted and dismissals
    innings_summary = innings_status.groupby('player_id').agg(
        innings_batted=('innings', 'count'),
        dismissals=('is_dismissed', 'sum')
    ).reset_index()
    innings_summary['not_outs'] = innings_summary['innings_batted'] - innings_summary['dismissals']

    # 3. Aggregate batting totals from ball_by_ball deliveries
    # Deliveries where player was striker
    striker_agg = bbb.groupby('striker_id').agg(
        total_runs=('runs', 'sum'),
        balls_faced=('is_ball_faced', 'sum'),
        fours=('is_four', 'sum'),
        sixes=('is_six', 'sum')
    ).reset_index().rename(columns={'striker_id': 'player_id'})

    # 4. Highest Score per batter
    # Runs per (player_id, match_id, innings)
    player_inn_runs = bbb.groupby(['striker_id', 'match_id', 'innings'])['runs'].sum().reset_index().rename(columns={'striker_id': 'player_id'})
    # Merge dismissal status to determine not out
    player_inn_runs = pd.merge(player_inn_runs, dismissed_unique, on=['match_id', 'innings', 'player_id'], how='left')
    player_inn_runs['is_out'] = player_inn_runs['is_dismissed'].astype('boolean').fillna(False).astype(bool)
    player_inn_runs['is_not_out'] = ~player_inn_runs['is_out']

    # Sort so that highest runs, then not-out comes first in case of tie
    player_inn_runs = player_inn_runs.sort_values(by=['player_id', 'runs', 'is_not_out'], ascending=[True, False, False])
    highest_scores = player_inn_runs.drop_duplicates(subset=['player_id'], keep='first').copy()
    highest_scores['highest_score'] = highest_scores['runs']
    highest_scores['highest_score_display'] = highest_scores.apply(
        lambda r: f"{int(r['runs'])}*" if r['is_not_out'] else f"{int(r['runs'])}", axis=1
    )
    hs_map = highest_scores[['player_id', 'highest_score', 'highest_score_display']].set_index('player_id')

    # 5. Competition breakdown (IPL vs T20I)
    ipl_bbb = bbb[bbb['tournament_type'] == 'IPL']
    ipl_agg = ipl_bbb.groupby('striker_id').agg(
        ipl_runs=('runs', 'sum'),
        ipl_balls_faced=('is_ball_faced', 'sum')
    ).reset_index().rename(columns={'striker_id': 'player_id'})

    t20i_bbb = bbb[bbb['tournament_type'] == 'T20I']
    t20i_agg = t20i_bbb.groupby('striker_id').agg(
        t20i_runs=('runs', 'sum'),
        t20i_balls_faced=('is_ball_faced', 'sum')
    ).reset_index().rename(columns={'striker_id': 'player_id'})

    # 6. Combine all metrics starting from all players who batted
    batters_df = pd.merge(innings_summary, striker_agg, on='player_id', how='left')
    batters_df['total_runs'] = batters_df['total_runs'].fillna(0).astype('int64')
    batters_df['balls_faced'] = batters_df['balls_faced'].fillna(0).astype('int64')
    batters_df['fours'] = batters_df['fours'].fillna(0).astype('int64')
    batters_df['sixes'] = batters_df['sixes'].fillna(0).astype('int64')

    # Attach player name
    batters_df['player_name'] = batters_df['player_id'].apply(registry.get_player_name)

    # Attach matches played
    batters_df['matches_played'] = batters_df['player_id'].map(player_matches).fillna(0).astype('int64')

    # Attach highest score
    batters_df['highest_score'] = batters_df['player_id'].map(hs_map['highest_score']).fillna(0).astype('int64')
    batters_df['highest_score_display'] = batters_df['player_id'].map(hs_map['highest_score_display']).fillna('0*')

    # Merge IPL and T20I splits
    batters_df = pd.merge(batters_df, ipl_agg, on='player_id', how='left')
    batters_df['ipl_runs'] = batters_df['ipl_runs'].fillna(0).astype('int64')
    batters_df['ipl_balls_faced'] = batters_df['ipl_balls_faced'].fillna(0).astype('int64')

    batters_df = pd.merge(batters_df, t20i_agg, on='player_id', how='left')
    batters_df['t20i_runs'] = batters_df['t20i_runs'].fillna(0).astype('int64')
    batters_df['t20i_balls_faced'] = batters_df['t20i_balls_faced'].fillna(0).astype('int64')

    # 7. Calculate derived rate statistics
    # Batting average = Total runs / Dismissals
    batters_df['batting_average'] = np.where(
        batters_df['dismissals'] > 0,
        (batters_df['total_runs'] / batters_df['dismissals']).round(2),
        np.nan
    )

    # Strike rate = (Total runs / Balls faced) * 100
    batters_df['strike_rate'] = np.where(
        batters_df['balls_faced'] > 0,
        ((batters_df['total_runs'] / batters_df['balls_faced']) * 100).round(2),
        0.0
    )

    # IPL strike rate
    batters_df['ipl_strike_rate'] = np.where(
        batters_df['ipl_balls_faced'] > 0,
        ((batters_df['ipl_runs'] / batters_df['ipl_balls_faced']) * 100).round(2),
        0.0
    )

    # T20I strike rate
    batters_df['t20i_strike_rate'] = np.where(
        batters_df['t20i_balls_faced'] > 0,
        ((batters_df['t20i_runs'] / batters_df['t20i_balls_faced']) * 100).round(2),
        0.0
    )

    # Boundary percentage
    # Standard: percentage of total runs scored from boundaries (fours * 4 + sixes * 6) / total_runs
    boundary_runs = (batters_df['fours'] * 4) + (batters_df['sixes'] * 6)
    batters_df['boundary_percentage'] = np.where(
        batters_df['total_runs'] > 0,
        ((boundary_runs / batters_df['total_runs']) * 100).round(2),
        0.0
    )
    batters_df['boundary_balls_percentage'] = np.where(
        batters_df['balls_faced'] > 0,
        (((batters_df['fours'] + batters_df['sixes']) / batters_df['balls_faced']) * 100).round(2),
        0.0
    )

    # Order columns logically
    ordered_cols = [
        'player_id',
        'player_name',
        'matches_played',
        'innings_batted',
        'total_runs',
        'balls_faced',
        'batting_average',
        'strike_rate',
        'fours',
        'sixes',
        'boundary_percentage',
        'boundary_balls_percentage',
        'dismissals',
        'not_outs',
        'highest_score',
        'highest_score_display',
        'ipl_runs',
        'ipl_balls_faced',
        'ipl_strike_rate',
        't20i_runs',
        't20i_balls_faced',
        't20i_strike_rate'
    ]
    batters_df = batters_df[ordered_cols].sort_values(by='total_runs', ascending=False).reset_index(drop=True)
    logger.info(f"Successfully built statistics for {len(batters_df)} eligible batters.")
    return batters_df
