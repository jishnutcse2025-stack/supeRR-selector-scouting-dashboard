"""
Data Loader Module for SupeRR Selector Cricket Analytics Engine.
Handles zip extraction, path resolution, and robust CSV loading.
"""

import os
import zipfile
import logging
import pandas as pd
from typing import Dict, Optional

logger = logging.getLogger(__name__)

DATA_FILES = {
    'competitions': 'competitions.csv',
    'teams': 'teams.csv',
    'matches': 'matches.csv',
    'ball_by_ball': 'ball_by_ball.csv',
    'mapping': 'competition_team_player_mapping.csv',
    'playing_eleven': 'playing_eleven.csv',
}


def resolve_data_directory(base_dir: str = '.') -> str:
    """
    Locates the directory containing the dataset CSVs.
    If only the ZIP file exists, extracts it automatically.
    """
    candidates = [
        os.path.join(base_dir, 'Data Pack'),
        os.path.join(base_dir, 'data_pack'),
        os.path.join(base_dir, 'data'),
        base_dir
    ]
    
    for candidate in candidates:
        if os.path.isdir(candidate):
            # Check if key CSV exists
            if os.path.exists(os.path.join(candidate, 'competitions.csv')):
                logger.info(f"Located data directory: {candidate}")
                return candidate
                
    # If not found, look for zip files to extract
    zip_candidates = [
        os.path.join(base_dir, 'data_pack.zip'),
        os.path.join(base_dir, '6af458274c1e8_data_pack.zip')
    ]
    for zpath in zip_candidates:
        if os.path.isfile(zpath):
            logger.info(f"Extracting dataset archive: {zpath}")
            with zipfile.ZipFile(zpath, 'r') as zf:
                zf.extractall(base_dir)
            # Recheck
            for candidate in candidates:
                if os.path.isdir(candidate) and os.path.exists(os.path.join(candidate, 'competitions.csv')):
                    logger.info(f"Extracted and located data directory: {candidate}")
                    return candidate

    raise FileNotFoundError("Could not locate cricket dataset CSVs or ZIP archive.")


def load_datasets(data_dir: Optional[str] = None) -> Dict[str, pd.DataFrame]:
    """
    Loads all six core CSV files into Pandas DataFrames with optimized dtypes.
    """
    if data_dir is None:
        data_dir = resolve_data_directory()

    logger.info(f"Loading datasets from: {data_dir}")
    dfs = {}

    # 1. competitions
    comp_path = os.path.join(data_dir, DATA_FILES['competitions'])
    dfs['competitions'] = pd.read_csv(
        comp_path,
        dtype={'comp_id': 'int64', 'comp_name': 'str', 'match_format': 'str', 'season': 'str'}
    )
    logger.info(f"Loaded competitions: {dfs['competitions'].shape[0]} records")

    # 2. teams
    teams_path = os.path.join(data_dir, DATA_FILES['teams'])
    dfs['teams'] = pd.read_csv(
        teams_path,
        dtype={'comp_id': 'int64', 'team_id': 'int64', 'team_name': 'str'}
    )
    logger.info(f"Loaded teams: {dfs['teams'].shape[0]} records")

    # 3. matches
    matches_path = os.path.join(data_dir, DATA_FILES['matches'])
    dfs['matches'] = pd.read_csv(
        matches_path,
        parse_dates=['match_date']
    )
    logger.info(f"Loaded matches: {dfs['matches'].shape[0]} records")

    # 4. competition_team_player_mapping
    map_path = os.path.join(data_dir, DATA_FILES['mapping'])
    dfs['mapping'] = pd.read_csv(
        map_path,
        dtype={
            'comp_id': 'int64',
            'comp_name': 'str',
            'team_id': 'int64',
            'team_name': 'str',
            'player_id': 'int64',
            'player_name': 'str'
        }
    )
    logger.info(f"Loaded player mapping: {dfs['mapping'].shape[0]} records")

    # 5. playing_eleven
    p11_path = os.path.join(data_dir, DATA_FILES['playing_eleven'])
    dfs['playing_eleven'] = pd.read_csv(
        p11_path,
        dtype={
            'match_id': 'int64',
            'team_id': 'int64',
            'player_id': 'int64',
            'batting_order': 'float64',
            'is_played': 'bool',
            'is_captain': 'boolean',
            'is_wk': 'boolean',
            'is_impact': 'int64',
            'is_impact_off': 'int64'
        }
    )
    logger.info(f"Loaded playing_eleven: {dfs['playing_eleven'].shape[0]} records")

    # 6. ball_by_ball
    bbb_path = os.path.join(data_dir, DATA_FILES['ball_by_ball'])
    logger.info(f"Loading ball_by_ball deliveries (~41 MB)...")
    dfs['ball_by_ball'] = pd.read_csv(
        bbb_path,
        low_memory=False,
        dtype={
            'match_id': 'int64',
            'innings': 'int64',
            'overid': 'int64',
            'over_ball_num': 'int64',
            'innings_ball_num': 'int64',
            'batting_team_id': 'int64',
            'bowling_team_id': 'int64',
            'striker_id': 'int64',
            'striker_name': 'str',
            'non_striker_id': 'int64',
            'non_striker_name': 'str',
            'bowler_id': 'int64',
            'bowler_name': 'str',
            'runs': 'int64',
            'is_four': 'bool',
            'is_six': 'bool',
            'is_wicket': 'bool',
            'extras1_runs': 'int64',
            'extras_2_runs': 'int64'
        }
    )
    logger.info(f"Loaded ball_by_ball: {dfs['ball_by_ball'].shape[0]} deliveries")

    return dfs
