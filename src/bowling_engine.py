"""
Bowling Engine Module for SupeRR Selector Cricket Analytics Engine.
Calculates comprehensive, verified bowling statistics across IPL, T20I, and Combined formats.
"""

import logging
import pandas as pd
import numpy as np
from typing import Dict
from src.player_mapping import PlayerRegistry

logger = logging.getLogger(__name__)


def build_bowler_statistics(filtered_dfs: Dict[str, pd.DataFrame], registry: PlayerRegistry) -> pd.DataFrame:
    """
    Computes career bowling statistics for every eligible bowler in IPL (2022+) and T20I (2022+).
    """
    logger.info("Computing bowler statistics...")
    bbb = filtered_dfs['ball_by_ball']
    p11 = filtered_dfs['playing_eleven']

    # 1. Matches played per player (from confirmed Playing XI)
    p11_played = p11[p11['is_played'] == True]
    player_matches = p11_played.groupby('player_id')['match_id'].nunique().to_dict()

    # 2. Innings bowled per bowler
    innings_bowled_s = bbb.groupby('bowler_id').apply(
        lambda g: g[['match_id', 'innings']].drop_duplicates().shape[0],
        include_groups=False
    ).reset_index(name='innings_bowled').rename(columns={'bowler_id': 'player_id'})

    # 3. Overall Bowling Aggregations
    overall_agg = bbb.groupby('bowler_id').agg(
        legal_balls_bowled=('is_legal', 'sum'),
        runs_conceded=('bowler_runs', 'sum'),
        wickets=('is_bowler_wicket', 'sum'),
        dot_balls=('is_dot_ball_bowler', 'sum')
    ).reset_index().rename(columns={'bowler_id': 'player_id'})

    # 4. Maidens calculation:
    # A maiden is an over of 6 legal balls bowled by the bowler conceding 0 runs.
    over_groups = bbb.groupby(['match_id', 'innings', 'overid', 'bowler_id']).agg(
        legal_balls=('is_legal', 'sum'),
        runs=('bowler_runs', 'sum')
    ).reset_index()
    maiden_overs = over_groups[(over_groups['legal_balls'] == 6) & (over_groups['runs'] == 0)]
    maidens_count = maiden_overs.groupby('bowler_id').size().reset_index(name='maidens').rename(columns={'bowler_id': 'player_id'})

    # 5. Competition breakdown (IPL vs T20I)
    # IPL
    ipl_bbb = bbb[bbb['tournament_type'] == 'IPL']
    ipl_agg = ipl_bbb.groupby('bowler_id').agg(
        ipl_legal_balls=('is_legal', 'sum'),
        ipl_runs_conceded=('bowler_runs', 'sum'),
        ipl_wickets=('is_bowler_wicket', 'sum'),
        ipl_dot_balls=('is_dot_ball_bowler', 'sum')
    ).reset_index().rename(columns={'bowler_id': 'player_id'})

    # T20I
    t20i_bbb = bbb[bbb['tournament_type'] == 'T20I']
    t20i_agg = t20i_bbb.groupby('bowler_id').agg(
        t20i_legal_balls=('is_legal', 'sum'),
        t20i_runs_conceded=('bowler_runs', 'sum'),
        t20i_wickets=('is_bowler_wicket', 'sum'),
        t20i_dot_balls=('is_dot_ball_bowler', 'sum')
    ).reset_index().rename(columns={'bowler_id': 'player_id'})

    # 6. Combine all metrics
    bowlers_df = pd.merge(innings_bowled_s, overall_agg, on='player_id', how='left')
    bowlers_df = pd.merge(bowlers_df, maidens_count, on='player_id', how='left')
    bowlers_df['maidens'] = bowlers_df['maidens'].fillna(0).astype('int64')

    # Attach player name
    bowlers_df['player_name'] = bowlers_df['player_id'].apply(registry.get_player_name)

    # Attach matches played
    bowlers_df['matches_played'] = bowlers_df['player_id'].map(player_matches).fillna(0).astype('int64')

    # Merge IPL and T20I splits
    bowlers_df = pd.merge(bowlers_df, ipl_agg, on='player_id', how='left')
    bowlers_df['ipl_legal_balls'] = bowlers_df['ipl_legal_balls'].fillna(0).astype('int64')
    bowlers_df['ipl_runs_conceded'] = bowlers_df['ipl_runs_conceded'].fillna(0).astype('int64')
    bowlers_df['ipl_wickets'] = bowlers_df['ipl_wickets'].fillna(0).astype('int64')
    bowlers_df['ipl_dot_balls'] = bowlers_df['ipl_dot_balls'].fillna(0).astype('int64')

    bowlers_df = pd.merge(bowlers_df, t20i_agg, on='player_id', how='left')
    bowlers_df['t20i_legal_balls'] = bowlers_df['t20i_legal_balls'].fillna(0).astype('int64')
    bowlers_df['t20i_runs_conceded'] = bowlers_df['t20i_runs_conceded'].fillna(0).astype('int64')
    bowlers_df['t20i_wickets'] = bowlers_df['t20i_wickets'].fillna(0).astype('int64')
    bowlers_df['t20i_dot_balls'] = bowlers_df['t20i_dot_balls'].fillna(0).astype('int64')

    # 7. Formats and Rate Metrics
    # Overs formatted as standard cricket notation: completed_overs.balls
    bowlers_df['overs'] = bowlers_df['legal_balls_bowled'].apply(lambda b: f"{b // 6}.{b % 6}")
    bowlers_df['ipl_overs'] = bowlers_df['ipl_legal_balls'].apply(lambda b: f"{b // 6}.{b % 6}")
    bowlers_df['t20i_overs'] = bowlers_df['t20i_legal_balls'].apply(lambda b: f"{b // 6}.{b % 6}")

    # Decimal overs for rate calculations
    overs_decimal = bowlers_df['legal_balls_bowled'] / 6.0
    ipl_overs_decimal = bowlers_df['ipl_legal_balls'] / 6.0
    t20i_overs_decimal = bowlers_df['t20i_legal_balls'] / 6.0

    # Bowling Average = Runs conceded / Wickets
    bowlers_df['bowling_average'] = np.where(
        bowlers_df['wickets'] > 0,
        (bowlers_df['runs_conceded'] / bowlers_df['wickets']).round(2),
        np.nan
    )

    # Economy rate = Runs conceded / Overs (decimal)
    bowlers_df['economy_rate'] = np.where(
        bowlers_df['legal_balls_bowled'] > 0,
        (bowlers_df['runs_conceded'] / overs_decimal).round(2),
        np.nan
    )

    # Bowling strike rate = Legal balls / Wickets
    bowlers_df['bowling_strike_rate'] = np.where(
        bowlers_df['wickets'] > 0,
        (bowlers_df['legal_balls_bowled'] / bowlers_df['wickets']).round(2),
        np.nan
    )

    # Dot-ball percentage
    bowlers_df['dot_ball_percentage'] = np.where(
        bowlers_df['legal_balls_bowled'] > 0,
        ((bowlers_df['dot_balls'] / bowlers_df['legal_balls_bowled']) * 100).round(2),
        0.0
    )

    # IPL Rate metrics
    bowlers_df['ipl_bowling_average'] = np.where(
        bowlers_df['ipl_wickets'] > 0,
        (bowlers_df['ipl_runs_conceded'] / bowlers_df['ipl_wickets']).round(2),
        np.nan
    )
    bowlers_df['ipl_economy_rate'] = np.where(
        bowlers_df['ipl_legal_balls'] > 0,
        (bowlers_df['ipl_runs_conceded'] / ipl_overs_decimal).round(2),
        np.nan
    )
    bowlers_df['ipl_bowling_strike_rate'] = np.where(
        bowlers_df['ipl_wickets'] > 0,
        (bowlers_df['ipl_legal_balls'] / bowlers_df['ipl_wickets']).round(2),
        np.nan
    )
    bowlers_df['ipl_dot_ball_percentage'] = np.where(
        bowlers_df['ipl_legal_balls'] > 0,
        ((bowlers_df['ipl_dot_balls'] / bowlers_df['ipl_legal_balls']) * 100).round(2),
        0.0
    )

    # T20I Rate metrics
    bowlers_df['t20i_bowling_average'] = np.where(
        bowlers_df['t20i_wickets'] > 0,
        (bowlers_df['t20i_runs_conceded'] / bowlers_df['t20i_wickets']).round(2),
        np.nan
    )
    bowlers_df['t20i_economy_rate'] = np.where(
        bowlers_df['t20i_legal_balls'] > 0,
        (bowlers_df['t20i_runs_conceded'] / t20i_overs_decimal).round(2),
        np.nan
    )
    bowlers_df['t20i_bowling_strike_rate'] = np.where(
        bowlers_df['t20i_wickets'] > 0,
        (bowlers_df['t20i_legal_balls'] / bowlers_df['t20i_wickets']).round(2),
        np.nan
    )
    bowlers_df['t20i_dot_ball_percentage'] = np.where(
        bowlers_df['t20i_legal_balls'] > 0,
        ((bowlers_df['t20i_dot_balls'] / bowlers_df['t20i_legal_balls']) * 100).round(2),
        0.0
    )

    ordered_cols = [
        'player_id',
        'player_name',
        'matches_played',
        'innings_bowled',
        'legal_balls_bowled',
        'overs',
        'runs_conceded',
        'wickets',
        'bowling_average',
        'economy_rate',
        'bowling_strike_rate',
        'dot_balls',
        'dot_ball_percentage',
        'maidens',
        'ipl_overs',
        'ipl_legal_balls',
        'ipl_runs_conceded',
        'ipl_wickets',
        'ipl_bowling_average',
        'ipl_economy_rate',
        'ipl_bowling_strike_rate',
        't20i_overs',
        't20i_legal_balls',
        't20i_runs_conceded',
        't20i_wickets',
        't20i_bowling_average',
        't20i_economy_rate',
        't20i_bowling_strike_rate'
    ]
    bowlers_df = bowlers_df[ordered_cols].sort_values(by=['wickets', 'economy_rate'], ascending=[False, True]).reset_index(drop=True)
    logger.info(f"Successfully built statistics for {len(bowlers_df)} eligible bowlers.")
    return bowlers_df
