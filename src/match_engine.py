"""
Match Engine Module for SupeRR Selector Cricket Analytics Engine.
Builds the player-match level dataset (player_match_statistics.csv).
Each row represents one player in one match, accurately reconciling batting,
bowling, and participation metrics.
"""

import logging
import pandas as pd
import numpy as np
from typing import Dict
from src.player_mapping import PlayerRegistry

logger = logging.getLogger(__name__)


def build_player_match_statistics(filtered_dfs: Dict[str, pd.DataFrame], registry: PlayerRegistry) -> pd.DataFrame:
    """
    Builds a granular player-level match dataset for every confirmed player in every eligible match.
    """
    logger.info("Building player_match_statistics...")
    matches = filtered_dfs['matches']
    bbb = filtered_dfs['ball_by_ball']
    p11 = filtered_dfs['playing_eleven']

    # 1. Base population: all confirmed participants in the Playing XI (is_played == True)
    # Deduplicate (match_id, player_id) to avoid match inflation from raw data duplicates
    base_p11_cols = ['match_id', 'team_id', 'player_id', 'batting_order', 'is_played', 'is_captain', 'is_wk', 'is_impact', 'is_impact_off']
    p11_clean = p11[p11['is_played'] == True][base_p11_cols].sort_values(
        by=['match_id', 'player_id', 'is_impact', 'batting_order'],
        ascending=[True, True, False, True]
    ).drop_duplicates(subset=['match_id', 'player_id'], keep='first').copy()

    # 2. Attach Match Information
    match_cols = ['match_id', 'match_date', 'comp_name', 'season', 'tournament_type', 'home_team_id', 'home_team', 'away_team_id', 'away_team']
    p11_merged = pd.merge(p11_clean, matches[match_cols], on='match_id', how='inner')

    # Resolve Team and Opponent
    def get_team_and_opponent(row):
        tid = row['team_id']
        htid = row['home_team_id']
        atid = row['away_team_id']
        
        team_name = registry.get_team_name(tid)
        if tid == htid:
            opp_id = atid
            opp_name = row['away_team'] if pd.notnull(row['away_team']) else registry.get_team_name(atid)
        else:
            opp_id = htid
            opp_name = row['home_team'] if pd.notnull(row['home_team']) else registry.get_team_name(htid)
        return pd.Series([team_name, opp_name], index=['team', 'opponent'])

    team_opp_df = p11_merged.apply(get_team_and_opponent, axis=1)
    p11_merged['team'] = team_opp_df['team']
    p11_merged['opponent'] = team_opp_df['opponent']

    # 3. Calculate Batting stats per (match_id, player_id)
    bat_match = bbb.groupby(['match_id', 'striker_id']).agg(
        runs=('runs', 'sum'),
        balls_faced=('is_ball_faced', 'sum'),
        fours=('is_four', 'sum'),
        sixes=('is_six', 'sum')
    ).reset_index().rename(columns={'striker_id': 'player_id'})

    # Identify did_bat: striker or non-striker or dismissed in that match
    strikers_m = bbb[['match_id', 'striker_id']].rename(columns={'striker_id': 'player_id'}).drop_duplicates()
    non_strikers_m = bbb[['match_id', 'non_striker_id']].rename(columns={'non_striker_id': 'player_id'}).drop_duplicates()
    dismissed_m = bbb[bbb['is_wicket'] == True][['match_id', 'dismissed_player_id']].dropna()
    dismissed_m['dismissed_player_id'] = dismissed_m['dismissed_player_id'].astype('int64')
    dismissed_m = dismissed_m.rename(columns={'dismissed_player_id': 'player_id'}).drop_duplicates()
    
    batted_players_m = pd.concat([strikers_m, non_strikers_m, dismissed_m]).drop_duplicates()
    batted_players_m['did_bat'] = True

    # 4. Calculate Bowling stats per (match_id, player_id)
    bowl_match = bbb.groupby(['match_id', 'bowler_id']).agg(
        wickets=('is_bowler_wicket', 'sum'),
        legal_balls_bowled=('is_legal', 'sum'),
        runs_conceded=('bowler_runs', 'sum')
    ).reset_index().rename(columns={'bowler_id': 'player_id'})
    bowl_match['did_bowl'] = True

    # 5. Merge Batting and Bowling into Base Population
    res = pd.merge(p11_merged, bat_match, on=['match_id', 'player_id'], how='left')
    res = pd.merge(res, batted_players_m, on=['match_id', 'player_id'], how='left')
    res = pd.merge(res, bowl_match, on=['match_id', 'player_id'], how='left')

    # Fill NaNs for players who did not bat or bowl
    res['runs'] = res['runs'].fillna(0).astype('int64')
    res['balls_faced'] = res['balls_faced'].fillna(0).astype('int64')
    res['fours'] = res['fours'].fillna(0).astype('int64')
    res['sixes'] = res['sixes'].fillna(0).astype('int64')
    res['did_bat'] = res['did_bat'].astype('boolean').fillna(False).astype(bool)

    res['wickets'] = res['wickets'].fillna(0).astype('int64')
    res['legal_balls_bowled'] = res['legal_balls_bowled'].fillna(0).astype('int64')
    res['runs_conceded'] = res['runs_conceded'].fillna(0).astype('int64')
    res['did_bowl'] = res['did_bowl'].astype('boolean').fillna(False).astype(bool)

    # Attach player name
    res['player_name'] = res['player_id'].apply(registry.get_player_name)

    # Format output columns
    res = res.rename(columns={
        'comp_name': 'competition',
        'tournament_type': 'format'
    })

    ordered_cols = [
        'match_id',
        'match_date',
        'competition',
        'season',
        'format',
        'player_id',
        'player_name',
        'team',
        'opponent',
        'runs',
        'balls_faced',
        'fours',
        'sixes',
        'wickets',
        'legal_balls_bowled',
        'runs_conceded',
        'batting_order',
        'is_captain',
        'is_wk',
        'is_impact',
        'is_impact_off',
        'did_bat',
        'did_bowl'
    ]

    res = res[ordered_cols].sort_values(by=['match_date', 'match_id', 'team', 'batting_order']).reset_index(drop=True)
    logger.info(f"Successfully built player_match_statistics: {len(res)} player-match rows.")
    return res
