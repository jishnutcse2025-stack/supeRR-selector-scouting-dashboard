"""
Data Cleaning and Data Quality Module for SupeRR Selector Cricket Analytics Engine.
Performs data profiling, generates data quality reports, and standardizes delivery attributes.
"""

import os
import logging
import pandas as pd
import numpy as np
from typing import Dict, Tuple

logger = logging.getLogger(__name__)

BOWLER_WICKET_TYPES = ['Caught', 'Bowled', 'LBW', 'Stump', 'Hit Wicket']
NON_BOWLER_WICKET_TYPES = ['RunOut', 'Retire Out', 'Obstracting the field', 'Obstructing the field']


def generate_data_quality_report(dfs: Dict[str, pd.DataFrame], output_path: str = 'outputs/data_quality_report.csv') -> pd.DataFrame:
    """
    Analyzes all loaded dataframes and compiles a comprehensive column-level quality report.
    """
    records = []
    for table_name, df in dfs.items():
        total_rows = len(df)
        for col in df.columns:
            null_count = int(df[col].isnull().sum())
            null_pct = round((null_count / total_rows) * 100, 2) if total_rows > 0 else 0.0
            unique_count = int(df[col].nunique())
            dtype_str = str(df[col].dtype)
            sample_val = str(df[col].dropna().iloc[0]) if unique_count > 0 else 'N/A'
            if len(sample_val) > 40:
                sample_val = sample_val[:37] + '...'

            records.append({
                'table_name': table_name,
                'column_name': col,
                'data_type': dtype_str,
                'total_records': total_rows,
                'missing_count': null_count,
                'missing_pct': null_pct,
                'unique_count': unique_count,
                'sample_value': sample_val
            })

    report_df = pd.DataFrame(records)
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    report_df.to_csv(output_path, index=False)
    logger.info(f"Generated Data Quality Report at {output_path} ({len(report_df)} columns profiled)")
    return report_df


def clean_and_enrich_deliveries(bbb_df: pd.DataFrame) -> pd.DataFrame:
    """
    Adds standardized, verified cricket rules columns to ball_by_ball records:
    - is_legal: True if ball is not wide and not no-ball (Overstep / other)
    - is_ball_faced: True if ball counts towards batter's balls faced (not a wide)
    - bowler_runs: Exact runs charged to the bowler
    - is_bowler_wicket: True if dismissal is credited to the bowler
    - is_dot_ball_bowler: True if delivery was legal and conceded 0 runs
    - delivery_total_runs: Complete team runs on delivery (bat + extras)
    """
    logger.info("Enriching delivery records with official cricket rules logic...")
    df = bbb_df.copy()

    # 1. Extras normalization
    # extras_type: NaN, wide, legbyes, Overstep, byes, other, Penalty
    df['extras_type_clean'] = df['extras_type'].fillna('none').astype(str).str.strip()

    # 2. Legal delivery: MCC Law - wides and no-balls are not legal balls in the over
    # Overstep and other represent no-balls
    df['is_legal'] = ~df['extras_type_clean'].isin(['wide', 'Overstep', 'other'])

    # 3. Balls faced by batter: wide deliveries are NOT faced by batter. No-balls ARE faced.
    df['is_ball_faced'] = df['extras_type_clean'] != 'wide'

    # 4. Bowler runs conceded:
    # - If wide: bowler charged wide extras + penalty runs + any overthrows
    # - If no-ball (Overstep or other): bowler charged batter runs + 1 no-ball penalty (extras1_runs).
    #   Byes/leg-byes off no-balls (extras_2_runs) are NOT charged to the bowler.
    # - Byes, leg-byes, penalty: NOT charged to bowler (only bat runs if any, which is 0)
    # - Regular delivery: batter runs off the bat
    def compute_bowler_runs(row):
        etype = row['extras_type_clean']
        runs = row['runs']
        if etype == 'wide':
            return runs + row['extras1_runs'] + row['extras_2_runs']
        elif etype in ['Overstep', 'other']:
            return runs + row['extras1_runs']
        elif etype in ['byes', 'legbyes', 'Penalty']:
            return 0
        else:
            return runs

    df['bowler_runs'] = df.apply(compute_bowler_runs, axis=1)

    # 5. Bowler wicket:
    # Credit wickets: Caught, Bowled, LBW, Stump, Hit Wicket.
    # Exclude: RunOut, Retire Out, Obstructing the field.
    df['is_bowler_wicket'] = (df['is_wicket'] == True) & (df['dismissal_type'].isin(BOWLER_WICKET_TYPES))

    # 6. Dot balls for bowler:
    # Legal ball with 0 bowler runs conceded
    df['is_dot_ball_bowler'] = (df['is_legal'] == True) & (df['bowler_runs'] == 0)

    # 7. Total delivery runs for innings
    df['delivery_total_runs'] = df['runs'] + df['extras1_runs'] + df['extras_2_runs']

    return df
