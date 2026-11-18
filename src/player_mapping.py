"""
Player Mapping and Identity Module for SupeRR Selector Cricket Analytics Engine.
Ensures player_id serves as the authoritative primary key, preventing duplicate player
profiles across different teams and competitions.
"""

import logging
import pandas as pd
from typing import Dict, Optional

logger = logging.getLogger(__name__)


class PlayerRegistry:
    """
    Authoritative registry mapping player_id to unique canonical player_name,
    and team_id to team_name.
    """
    def __init__(self, mapping_df: pd.DataFrame, bbb_df: Optional[pd.DataFrame] = None, teams_df: Optional[pd.DataFrame] = None):
        self.player_map: Dict[int, str] = {}
        self.team_map: Dict[int, str] = {}
        self._build_registry(mapping_df, bbb_df, teams_df)

    def _build_registry(self, mapping_df: pd.DataFrame, bbb_df: Optional[pd.DataFrame], teams_df: Optional[pd.DataFrame]):
        # 1. From mapping df
        for _, row in mapping_df[['player_id', 'player_name']].drop_duplicates().iterrows():
            pid = int(row['player_id'])
            name = str(row['player_name']).strip()
            if pid not in self.player_map:
                self.player_map[pid] = name

        # 2. Check ball_by_ball for any unmapped strikers/bowlers
        if bbb_df is not None:
            strikers = bbb_df[['striker_id', 'striker_name']].drop_duplicates()
            for _, row in strikers.iterrows():
                pid = int(row['striker_id'])
                name = str(row['striker_name']).strip()
                if pid not in self.player_map:
                    self.player_map[pid] = name

            bowlers = bbb_df[['bowler_id', 'bowler_name']].drop_duplicates()
            for _, row in bowlers.iterrows():
                pid = int(row['bowler_id'])
                name = str(row['bowler_name']).strip()
                if pid not in self.player_map:
                    self.player_map[pid] = name

        # 3. Teams registry
        if teams_df is not None:
            for _, row in teams_df[['team_id', 'team_name']].drop_duplicates().iterrows():
                tid = int(row['team_id'])
                tname = str(row['team_name']).strip()
                if tid not in self.team_map:
                    self.team_map[tid] = tname

        logger.info(f"PlayerRegistry initialized with {len(self.player_map)} unique players and {len(self.team_map)} teams.")

    def get_player_name(self, player_id: int) -> str:
        return self.player_map.get(player_id, f"Unknown Player ({player_id})")

    def get_team_name(self, team_id: int) -> str:
        return self.team_map.get(team_id, f"Unknown Team ({team_id})")

    def get_player_df(self) -> pd.DataFrame:
        return pd.DataFrame([
            {'player_id': pid, 'player_name': name}
            for pid, name in self.player_map.items()
        ])


def build_player_registry(dfs: Dict[str, pd.DataFrame]) -> PlayerRegistry:
    return PlayerRegistry(dfs['mapping'], dfs.get('ball_by_ball'), dfs.get('teams'))
