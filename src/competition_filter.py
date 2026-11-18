"""
Competition Filter Module for SupeRR Selector Cricket Analytics Engine.
Filters dataset strictly to IPL (2022+) and T20I (2022+), excluding unrelated T20 tournaments.
"""

import logging
import pandas as pd
from typing import Dict, Tuple, Set

logger = logging.getLogger(__name__)


def identify_eligible_competitions(comp_df: pd.DataFrame) -> pd.DataFrame:
    """
    Identifies eligible competitions based on competition records:
    1. IPL: Identified by comp_name containing 'IPL' or 'Indian Premier League'
       Seasons: 2022 onwards (IPL 2022, 2023, 2024, 2025, 2026).
    2. T20I: Identified by match_format == 'T20I'
       Seasons: 2022 onwards.
    
    Explicitly excludes other T20 leagues/tournaments (e.g., Mens T20 Emerging Teams Asia Cup).
    """
    df = comp_df.copy()
    
    # Identify IPL
    is_ipl = df['comp_name'].str.contains(r'\bIPL\b|Indian Premier League', case=False, na=False)
    
    # Identify T20I
    is_t20i = df['match_format'].str.upper() == 'T20I'
    
    # Parse seasons (all seasons in this dataset are >= 2022, e.g., '2022', '2022/23', etc.)
    # Confirm starting year >= 2022
    def extract_start_year(season_str):
        try:
            return int(str(season_str).split('/')[0])
        except (ValueError, TypeError, IndexError):
            return 0

    df['start_year'] = df['season'].apply(extract_start_year)
    is_2022_onwards = df['start_year'] >= 2022

    # Tag tournament type
    df['tournament_type'] = None
    df.loc[is_ipl & is_2022_onwards, 'tournament_type'] = 'IPL'
    df.loc[is_t20i & is_2022_onwards, 'tournament_type'] = 'T20I'

    eligible_df = df[df['tournament_type'].notnull()].copy()

    logger.info(f"Identified {len(eligible_df)} eligible competitions:")
    logger.info(f"  IPL Competitions: {int((eligible_df['tournament_type'] == 'IPL').sum())}")
    logger.info(f"  T20I Competitions: {int((eligible_df['tournament_type'] == 'T20I').sum())}")

    excluded_df = df[df['tournament_type'].isnull()]
    if not excluded_df.empty:
        logger.info(f"Explicitly excluded {len(excluded_df)} competitions: {excluded_df['comp_name'].tolist()}")

    return eligible_df


def filter_dataset_by_competition(dfs: Dict[str, pd.DataFrame]) -> Dict[str, pd.DataFrame]:
    """
    Filters all tables (competitions, matches, ball_by_ball, playing_eleven, mapping)
    to only include eligible competitions and matches.
    """
    eligible_comp = identify_eligible_competitions(dfs['competitions'])
    eligible_comp_ids = set(eligible_comp['comp_id'].unique())

    # Map competition info
    comp_info = eligible_comp[['comp_id', 'comp_name', 'season', 'tournament_type']].set_index('comp_id')

    # 1. Filter Matches
    matches = dfs['matches'].copy()
    matches_filtered = matches[matches['comp_id'].isin(eligible_comp_ids)].copy()
    matches_filtered['comp_name'] = matches_filtered['comp_id'].map(comp_info['comp_name'])
    matches_filtered['season'] = matches_filtered['comp_id'].map(comp_info['season'])
    matches_filtered['tournament_type'] = matches_filtered['comp_id'].map(comp_info['tournament_type'])
    matches_filtered['match_format'] = matches_filtered['tournament_type']

    eligible_match_ids = set(matches_filtered['match_id'].unique())
    logger.info(f"Filtered matches: {len(matches_filtered)} total eligible matches")
    logger.info(f"  IPL matches: {int((matches_filtered['tournament_type'] == 'IPL').sum())}")
    logger.info(f"  T20I matches: {int((matches_filtered['tournament_type'] == 'T20I').sum())}")

    # 2. Filter Ball by Ball
    bbb = dfs['ball_by_ball'].copy()
    bbb_filtered = bbb[bbb['match_id'].isin(eligible_match_ids)].copy()
    
    # Merge match metadata
    match_meta = matches_filtered[['match_id', 'comp_id', 'comp_name', 'season', 'tournament_type', 'match_date']]
    bbb_filtered = pd.merge(bbb_filtered, match_meta, on='match_id', how='inner')
    logger.info(f"Filtered ball_by_ball: {len(bbb_filtered)} deliveries across {bbb_filtered['match_id'].nunique()} matches")

    # 3. Filter Playing Eleven
    p11 = dfs['playing_eleven'].copy()
    p11_filtered = p11[p11['match_id'].isin(eligible_match_ids)].copy()
    p11_filtered = pd.merge(p11_filtered, match_meta, on='match_id', how='inner')
    logger.info(f"Filtered playing_eleven: {len(p11_filtered)} records across {p11_filtered['match_id'].nunique()} matches")

    # 4. Filter Mapping
    mapping = dfs['mapping'].copy()
    mapping_filtered = mapping[mapping['comp_id'].isin(eligible_comp_ids)].copy()
    mapping_filtered['tournament_type'] = mapping_filtered['comp_id'].map(comp_info['tournament_type'])

    # 5. Filter Teams
    teams = dfs['teams'].copy()
    teams_filtered = teams[teams['comp_id'].isin(eligible_comp_ids)].copy()

    return {
        'competitions': eligible_comp,
        'matches': matches_filtered,
        'ball_by_ball': bbb_filtered,
        'playing_eleven': p11_filtered,
        'mapping': mapping_filtered,
        'teams': teams_filtered
    }
