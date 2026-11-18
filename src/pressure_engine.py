"""
Pressure Performance Index (PPI) Engine for SupeRR Selector Season 2.
Computes ball-by-ball pre-delivery pressure scores, context-adjusted metrics (RVAE/RSAE),
tier-weighted shrinkage, multi-match consistency, and final Top 10 rankings.
"""

import os
import logging
import pandas as pd
import numpy as np
from scipy.stats import zscore
from typing import Dict, Tuple

logger = logging.getLogger(__name__)

# Full Member Team IDs in ICC T20I
FULL_MEMBER_IDS = {18, 20, 22, 19, 17, 25, 28, 27, 78, 21, 72, 23}


def assign_competition_tier_weight(matches_df: pd.DataFrame) -> pd.DataFrame:
    """
    Assigns competition tier weights:
    - Tier 1: IPL matches and Full-Member vs Full-Member internationals (weight = 1.00)
    - Tier 1.5: Full-Member vs Associate internationals (weight = 0.85)
    - Tier 2: Associate vs Associate internationals (weight = 0.70)
    """
    df = matches_df.copy()

    def calc_tier(row):
        if row.get('tournament_type') == 'IPL':
            return 1.00, 'Tier 1 (IPL)'
        is_h = row.get('home_team_id') in FULL_MEMBER_IDS
        is_a = row.get('away_team_id') in FULL_MEMBER_IDS
        if is_h and is_a:
            return 1.00, 'Tier 1 (FM vs FM)'
        elif is_h or is_a:
            return 0.85, 'Tier 1.5 (FM vs Assoc)'
        else:
            return 0.70, 'Tier 2 (Assoc vs Assoc)'

    tier_res = df.apply(calc_tier, axis=1)
    df['tier_weight'] = [t[0] for t in tier_res]
    df['tier_label'] = [t[1] for t in tier_res]
    return df


def compute_ball_by_ball_pressure(
    bbb_df: pd.DataFrame,
    matches_df: pd.DataFrame,
    innings_df: pd.DataFrame,
    hp_threshold: float = 65.0
) -> pd.DataFrame:
    """
    Computes a transparent, pre-delivery situational pressure score (0 to 100)
    for every legal/valid delivery in eligible matches.
    """
    logger.info("Computing pre-delivery situational pressure scores (0-100)...")
    bbb = bbb_df.sort_values(['match_id', 'innings', 'innings_ball_num']).copy()

    # 1. Match stakes and tier weights
    m_df = assign_competition_tier_weight(matches_df)
    m_df['is_knockout'] = (m_df['knock_out'] == 1) | m_df['stage'].isin(['Final', 'Qualifier', 'Eliminator', 'Semi Final'])
    m_cols = ['match_id', 'is_knockout', 'tier_weight', 'home_team', 'away_team']
    bbb = pd.merge(bbb, m_df[m_cols], on='match_id', how='left')

    # 2. Innings target and metadata
    inn_cols = ['match_id', 'innings_number', 'target']
    inn_sub = innings_df[inn_cols].rename(columns={'innings_number': 'innings'})
    bbb = pd.merge(bbb, inn_sub, on=['match_id', 'innings'], how='left')

    # 3. Cumulative Pre-Delivery Match State
    grp = bbb.groupby(['match_id', 'innings'])
    cum_legal = grp['is_legal'].cumsum()
    cum_runs = grp['delivery_total_runs'].cumsum()
    cum_wkts = grp['is_wicket'].cumsum()

    bbb['pre_legal_balls'] = cum_legal - bbb['is_legal'].astype(int)
    bbb['pre_runs'] = cum_runs - bbb['delivery_total_runs']
    bbb['pre_wkts'] = cum_wkts - bbb['is_wicket'].astype(int)
    bbb['pre_balls_rem'] = np.maximum(0, 120 - bbb['pre_legal_balls'])
    bbb['pre_wkts_rem'] = np.maximum(0, 10 - bbb['pre_wkts'])

    # 4. Phase Classification
    def get_phase(overid):
        if overid <= 6:
            return 'Powerplay'
        elif overid <= 15:
            return 'Middle'
        else:
            return 'Death'

    bbb['phase'] = bbb['overid'].apply(get_phase)
    phase_mult = bbb['phase'].map({'Powerplay': 1.00, 'Middle': 1.05, 'Death': 1.15})
    knockout_mult = np.where(bbb['is_knockout'], 1.15, 1.00)

    # 5. Innings 2 (Chasing Target) Formulation
    bbb['pre_runs_needed'] = np.maximum(0, bbb['target'] - bbb['pre_runs'])
    bbb['pre_rrr'] = np.where(
        (bbb['pre_balls_rem'] > 0) & (bbb['pre_runs_needed'] > 0),
        (bbb['pre_runs_needed'] / bbb['pre_balls_rem']) * 6.0,
        0.0
    )

    # Base RRR pressure (normalized around T20 par 8.5)
    rrr_norm = np.clip(bbb['pre_rrr'] / 8.5, 0.0, 3.5)
    rate_pressure_inn2 = 45.0 * (rrr_norm ** 1.15)
    resource_factor_inn2 = 0.70 + (0.06 * bbb['pre_wkts'])
    urgency_factor_inn2 = 0.85 + (0.35 * ((120 - bbb['pre_balls_rem']) / 120.0))

    raw_p_inn2 = rate_pressure_inn2 * resource_factor_inn2 * urgency_factor_inn2 * phase_mult * knockout_mult
    raw_p_inn2 = np.where(bbb['pre_runs_needed'] <= 0, 0.0, raw_p_inn2)

    # Dead-rubber / Hopeless chase tapering:
    # When RRR > 24.0 with <= 2 wickets remaining, win probability is near 0.
    # Taper pressure down so hopeless tail-end slogs don't artificially inflate ratings.
    raw_p_inn2 = np.where(
        (bbb['pre_rrr'] > 24.0) & (bbb['pre_wkts_rem'] <= 2),
        np.maximum(35.0, 55.0 - 0.8 * (bbb['pre_rrr'] - 24.0) - 5.0 * (2 - bbb['pre_wkts_rem'])),
        raw_p_inn2
    )

    # 6. Innings 1 (Setting Target) Formulation
    over_flt = bbb['overid'].astype(float)
    exp_wkts = 0.30 * over_flt
    delta_wkts = np.maximum(0.0, bbb['pre_wkts'] - exp_wkts)

    # Collapse Pressure: >= 2 wickets in Powerplay or >= 3 wickets before over 10
    collapse_bonus = np.where(
        (over_flt <= 6) & (bbb['pre_wkts'] >= 2),
        28.0 + 12.0 * (bbb['pre_wkts'] - 2),
        np.where(
            (over_flt <= 10) & (bbb['pre_wkts'] >= 3),
            32.0 + 10.0 * (bbb['pre_wkts'] - 3),
            np.minimum(40.0, 12.0 * delta_wkts)
        )
    )

    # Death-overs acceleration pressure (overs 16-20)
    death_accel = np.where(
        over_flt >= 16,
        55.0 + 7.5 * (over_flt - 16) + (3.0 * (bbb['pre_wkts_rem'] <= 3)),
        0.0
    )

    base_inn1 = np.where(over_flt <= 6, 35.0, np.where(over_flt <= 15, 42.0, 0.0))
    raw_p_inn1 = (base_inn1 + collapse_bonus + death_accel) * phase_mult * knockout_mult

    # 7. Unified Pressure Score
    pressure_score = np.where(
        bbb['innings'] == 1,
        raw_p_inn1,
        np.where(bbb['innings'] == 2, raw_p_inn2, 95.0)  # Super Overs = 95+
    )
    bbb['pressure_score'] = np.clip(pressure_score, 0.0, 100.0).round(1)
    bbb['is_high_pressure'] = bbb['pressure_score'] >= hp_threshold

    # 8. Empirical Pars (Innings, Phase, Over-by-Over)
    par_bat = bbb.groupby(['innings', 'phase', 'overid'])['runs'].mean().to_dict()
    par_bowl = bbb[bbb['is_legal']].groupby(['innings', 'phase', 'overid'])['bowler_runs'].mean().to_dict()

    bbb['par_bat_runs'] = bbb.set_index(['innings', 'phase', 'overid']).index.map(par_bat)
    bbb['par_bowl_runs'] = bbb.set_index(['innings', 'phase', 'overid']).index.map(par_bowl)

    # RVAE and RSAE with tier weighting
    bbb['rvae'] = (bbb['runs'] - bbb['par_bat_runs']) * bbb['tier_weight']
    bbb['rsae'] = (bbb['par_bowl_runs'] - bbb['bowler_runs']) * bbb['tier_weight']

    logger.info(f"Pressure scores calculated across {len(bbb):,} deliveries.")
    return bbb


def compute_batter_ppi(
    scored_bbb: pd.DataFrame,
    min_hp_balls: int = 150,
    min_hp_inns: int = 10,
    k_shrinkage: int = 100
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Computes Pressure Performance Index (PPI) for all eligible batters.
    Returns (all_batters_ppi, top10_batters).
    """
    logger.info("Computing Batter PPI rankings...")
    bbb = scored_bbb

    # 1. Batter Baseline Metrics (All legal deliveries faced)
    bat_base = bbb[bbb['is_ball_faced']].groupby('striker_id').agg(
        base_runs=('runs', 'sum'),
        base_balls=('runs', 'count'),
        base_dots=('runs', lambda x: (x == 0).sum()),
        base_dismissals=('is_wicket', 'sum')
    ).reset_index()
    bat_base['base_sr'] = (bat_base['base_runs'] / bat_base['base_balls'] * 100).round(2)
    bat_base['base_dot_avoid'] = (100.0 - (bat_base['base_dots'] / bat_base['base_balls'] * 100)).round(2)

    # 2. High-Pressure Batter Metrics
    hp_b = bbb[bbb['is_high_pressure'] & bbb['is_ball_faced']].copy()
    bat_hp = hp_b.groupby(['striker_id', 'striker_name']).agg(
        hp_balls=('runs', 'count'),
        hp_runs=('runs', 'sum'),
        hp_inns=('match_id', 'nunique'),
        hp_dots=('runs', lambda x: (x == 0).sum()),
        hp_fours=('is_four', 'sum'),
        hp_sixes=('is_six', 'sum'),
        hp_rvae=('rvae', 'sum'),
        hp_dismissals=('is_wicket', 'sum')
    ).reset_index()

    bat_hp = pd.merge(bat_hp, bat_base[['striker_id', 'base_sr', 'base_dot_avoid']], on='striker_id', how='left')

    # 3. Eligibility Filtering
    q_bat = bat_hp[(bat_hp['hp_balls'] >= min_hp_balls) & (bat_hp['hp_inns'] >= min_hp_inns)].copy()

    # Derived Rate Metrics
    q_bat['hp_sr'] = (q_bat['hp_runs'] / q_bat['hp_balls'] * 100).round(2)
    q_bat['delta_sr'] = (q_bat['hp_sr'] - q_bat['base_sr']).round(2)
    q_bat['rvae_per_ball'] = (q_bat['hp_rvae'] / q_bat['hp_balls']).round(3)
    q_bat['hp_dot_avoid'] = (100.0 - (q_bat['hp_dots'] / q_bat['hp_balls'] * 100)).round(2)
    q_bat['hp_boundary_pct'] = (((q_bat['hp_fours'] * 4 + q_bat['hp_sixes'] * 6) / q_bat['hp_runs']) * 100).round(2)
    q_bat['survival_rate'] = (q_bat['hp_balls'] / np.maximum(1, q_bat['hp_dismissals'])).round(2)

    # 4. Multi-match Consistency (Share of HP innings with positive RVAE)
    match_rvae = hp_b.groupby(['striker_id', 'match_id'])['rvae'].sum().reset_index()
    pos_inns = match_rvae[match_rvae['rvae'] > 0].groupby('striker_id').size().rename('pos_inns')
    tot_inns = match_rvae.groupby('striker_id').size().rename('tot_inns')
    consistency_df = pd.concat([pos_inns, tot_inns], axis=1).fillna(0)
    consistency_df['consistency'] = (consistency_df['pos_inns'] / consistency_df['tot_inns']).round(3)

    q_bat = pd.merge(q_bat, consistency_df[['consistency']], left_on='striker_id', right_index=True, how='left')

    # 5. Empirical Bayes Shrinkage (k = 100)
    pop_mean_rvae = q_bat['rvae_per_ball'].mean()
    q_bat['shrunk_rvae'] = (
        (q_bat['hp_balls'] / (q_bat['hp_balls'] + k_shrinkage)) * q_bat['rvae_per_ball'] +
        (k_shrinkage / (q_bat['hp_balls'] + k_shrinkage)) * pop_mean_rvae
    ).round(3)

    # 6. Composite PPI Scoring
    z_rvae = zscore(q_bat['shrunk_rvae'])
    z_sr = zscore(q_bat['hp_sr'])
    z_dsr = zscore(q_bat['delta_sr'])
    z_dot = zscore(q_bat['hp_dot_avoid'])
    z_bnd = zscore(q_bat['hp_boundary_pct'])
    z_surv = zscore(np.log1p(q_bat['survival_rate']))
    z_con = zscore(q_bat['consistency'])

    # Weighted multi-factor Z-score
    raw_ppi = (
        0.30 * z_rvae +
        0.20 * z_sr +
        0.15 * z_dsr +
        0.10 * z_dot +
        0.10 * z_bnd +
        0.05 * z_surv +
        0.10 * z_con
    )
    q_bat['ppi_raw'] = raw_ppi
    min_p, max_p = raw_ppi.min(), raw_ppi.max()
    q_bat['ppi_score'] = ((raw_ppi - min_p) / (max_p - min_p) * 60.0 + 40.0).round(2)

    # Sort & Rank
    q_bat = q_bat.sort_values('ppi_score', ascending=False).reset_index(drop=True)
    q_bat['rank'] = range(1, len(q_bat) + 1)

    top10_batters = q_bat.head(10).copy()
    logger.info(f"Batter PPI complete: {len(q_bat)} eligible batters ranked.")
    return q_bat, top10_batters


def compute_bowler_ppi(
    scored_bbb: pd.DataFrame,
    min_hp_balls: int = 120,
    min_hp_inns: int = 10,
    k_shrinkage: int = 100
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Computes Pressure Performance Index (PPI) for all eligible bowlers.
    Returns (all_bowlers_ppi, top10_bowlers).
    """
    logger.info("Computing Bowler PPI rankings...")
    bbb = scored_bbb

    # 1. Bowler Baseline Metrics (All legal balls bowled)
    bowl_base = bbb[bbb['is_legal']].groupby('bowler_id').agg(
        base_runs=('bowler_runs', 'sum'),
        base_balls=('bowler_runs', 'count'),
        base_dots=('bowler_runs', lambda x: (x == 0).sum())
    ).reset_index()
    bowl_base['base_econ'] = (bowl_base['base_runs'] / (bowl_base['base_balls'] / 6.0)).round(2)
    bowl_base['base_dot_pct'] = (bowl_base['base_dots'] / bowl_base['base_balls'] * 100).round(2)

    # 2. High-Pressure Bowler Metrics
    hp_bw = bbb[bbb['is_high_pressure'] & bbb['is_legal']].copy()
    bowl_hp = hp_bw.groupby(['bowler_id', 'bowler_name']).agg(
        hp_balls=('bowler_runs', 'count'),
        hp_runs=('bowler_runs', 'sum'),
        hp_inns=('match_id', 'nunique'),
        hp_dots=('bowler_runs', lambda x: (x == 0).sum()),
        hp_wickets=('is_bowler_wicket', 'sum'),
        hp_rsae=('rsae', 'sum'),
        tier_weight_sum=('tier_weight', 'sum')
    ).reset_index()

    bowl_hp = pd.merge(bowl_hp, bowl_base[['bowler_id', 'base_econ', 'base_dot_pct']], on='bowler_id', how='left')

    # 3. Eligibility Filtering
    q_bowl = bowl_hp[(bowl_hp['hp_balls'] >= min_hp_balls) & (bowl_hp['hp_inns'] >= min_hp_inns)].copy()

    # Derived Rate Metrics
    q_bowl['hp_econ'] = (q_bowl['hp_runs'] / (q_bowl['hp_balls'] / 6.0)).round(2)
    q_bowl['hp_dot_pct'] = (q_bowl['hp_dots'] / q_bowl['hp_balls'] * 100).round(2)
    q_bowl['rsae_per_ball'] = (q_bowl['hp_rsae'] / q_bowl['hp_balls']).round(3)
    q_bowl['hp_wkt_sr'] = (q_bowl['hp_balls'] / np.maximum(1, q_bowl['hp_wickets'])).round(2)
    q_bowl['hp_wkt_rate'] = (q_bowl['hp_wickets'] / q_bowl['hp_balls'] * 100).round(2)
    q_bowl['delta_econ'] = (q_bowl['base_econ'] - q_bowl['hp_econ']).round(2)

    # 4. Multi-match Consistency (Share of HP bowling spells with positive RSAE)
    match_rsae = hp_bw.groupby(['bowler_id', 'match_id'])['rsae'].sum().reset_index()
    pos_inns = match_rsae[match_rsae['rsae'] > 0].groupby('bowler_id').size().rename('pos_inns')
    tot_inns = match_rsae.groupby('bowler_id').size().rename('tot_inns')
    consistency_df = pd.concat([pos_inns, tot_inns], axis=1).fillna(0)
    consistency_df['consistency'] = (consistency_df['pos_inns'] / consistency_df['tot_inns']).round(3)

    q_bowl = pd.merge(q_bowl, consistency_df[['consistency']], left_on='bowler_id', right_index=True, how='left')

    # 5. Empirical Bayes Shrinkage (k = 100)
    pop_mean_rsae = q_bowl['rsae_per_ball'].mean()
    q_bowl['shrunk_rsae'] = (
        (q_bowl['hp_balls'] / (q_bowl['hp_balls'] + k_shrinkage)) * q_bowl['rsae_per_ball'] +
        (k_shrinkage / (q_bowl['hp_balls'] + k_shrinkage)) * pop_mean_rsae
    ).round(3)

    # Volume credibility factor (log-scaled volume multiplier to reward extensive proven volume)
    vol_factor = np.log10(q_bowl['hp_balls']) / np.log10(1000)
    vol_factor = np.clip(vol_factor, 0.70, 1.05)

    # 6. Composite PPI Scoring
    z_rsae = zscore(q_bowl['shrunk_rsae'])
    z_econ = -zscore(q_bowl['hp_econ'])  # Lower economy is better
    z_dot = zscore(q_bowl['hp_dot_pct'])
    z_wkt = zscore(q_bowl['hp_wkt_rate'])
    z_con = zscore(q_bowl['consistency'])

    raw_ppi = (
        0.35 * z_rsae +
        0.25 * z_econ +
        0.15 * z_dot +
        0.15 * z_wkt +
        0.10 * z_con
    ) * vol_factor

    q_bowl['ppi_raw'] = raw_ppi
    min_p, max_p = raw_ppi.min(), raw_ppi.max()
    q_bowl['ppi_score'] = ((raw_ppi - min_p) / (max_p - min_p) * 60.0 + 40.0).round(2)

    # Sort & Rank
    q_bowl = q_bowl.sort_values('ppi_score', ascending=False).reset_index(drop=True)
    q_bowl['rank'] = range(1, len(q_bowl) + 1)

    top10_bowlers = q_bowl.head(10).copy()
    logger.info(f"Bowler PPI complete: {len(q_bowl)} eligible bowlers ranked.")
    return q_bowl, top10_bowlers


def extract_pressure_case_studies(
    scored_bbb: pd.DataFrame,
    top_batters: pd.DataFrame,
    top_bowlers: pd.DataFrame
) -> pd.DataFrame:
    """
    Extracts representative match-winning high-pressure performances for each Top 10 player.
    """
    logger.info("Extracting high-pressure case studies for Top 10 players...")
    case_studies = []

    # Batters Case Studies
    for _, batter in top_batters.iterrows():
        pid = batter['striker_id']
        name = batter['striker_name']
        b_balls = scored_bbb[(scored_bbb['striker_id'] == pid) & (scored_bbb['is_high_pressure']) & (scored_bbb['is_ball_faced'])]
        
        # Group by match to find peak high-pressure contribution
        m_perf = b_balls.groupby('match_id').agg(
            hp_runs=('runs', 'sum'),
            hp_balls=('runs', 'count'),
            hp_fours=('is_four', 'sum'),
            hp_sixes=('is_six', 'sum'),
            hp_rvae=('rvae', 'sum'),
            comp_name=('comp_name', 'first'),
            match_date=('match_date', 'first'),
            tournament_type=('tournament_type', 'first'),
            home_team=('home_team', 'first'),
            away_team=('away_team', 'first'),
            avg_pressure=('pressure_score', 'mean')
        ).reset_index()

        if not m_perf.empty:
            best_match = m_perf.sort_values(by=['hp_rvae', 'hp_runs'], ascending=[False, False]).iloc[0]
            sr = round((best_match['hp_runs'] / best_match['hp_balls']) * 100, 1)
            case_studies.append({
                'category': 'Batter',
                'rank': batter['rank'],
                'player_id': pid,
                'player_name': name,
                'ppi_score': batter['ppi_score'],
                'match_id': best_match['match_id'],
                'match_date': str(best_match['match_date'])[:10],
                'competition': best_match['comp_name'],
                'format': best_match['tournament_type'],
                'matchup': f"{best_match['home_team']} vs {best_match['away_team']}",
                'hp_performance': f"{int(best_match['hp_runs'])} runs off {int(best_match['hp_balls'])} balls (SR {sr})",
                'boundaries': f"{int(best_match['hp_fours'])}x4, {int(best_match['hp_sixes'])}x6",
                'rvae_generated': round(best_match['hp_rvae'], 2),
                'mean_pressure_score': round(best_match['avg_pressure'], 1),
                'context_impact': 'High-leverage acceleration in death/collapse situation yielding decisive match advantage.'
            })

    # Bowlers Case Studies
    for _, bowler in top_bowlers.iterrows():
        pid = bowler['bowler_id']
        name = bowler['bowler_name']
        b_balls = scored_bbb[(scored_bbb['bowler_id'] == pid) & (scored_bbb['is_high_pressure']) & (scored_bbb['is_legal'])]

        m_perf = b_balls.groupby('match_id').agg(
            hp_runs=('bowler_runs', 'sum'),
            hp_balls=('bowler_runs', 'count'),
            hp_wickets=('is_bowler_wicket', 'sum'),
            hp_dots=('bowler_runs', lambda x: (x == 0).sum()),
            hp_rsae=('rsae', 'sum'),
            comp_name=('comp_name', 'first'),
            match_date=('match_date', 'first'),
            tournament_type=('tournament_type', 'first'),
            home_team=('home_team', 'first'),
            away_team=('away_team', 'first'),
            avg_pressure=('pressure_score', 'mean')
        ).reset_index()

        if not m_perf.empty:
            best_match = m_perf.sort_values(by=['hp_rsae', 'hp_wickets'], ascending=[False, False]).iloc[0]
            econ = round((best_match['hp_runs'] / (best_match['hp_balls'] / 6.0)), 2)
            overs = f"{best_match['hp_balls'] // 6}.{best_match['hp_balls'] % 6}"
            case_studies.append({
                'category': 'Bowler',
                'rank': bowler['rank'],
                'player_id': pid,
                'player_name': name,
                'ppi_score': bowler['ppi_score'],
                'match_id': best_match['match_id'],
                'match_date': str(best_match['match_date'])[:10],
                'competition': best_match['comp_name'],
                'format': best_match['tournament_type'],
                'matchup': f"{best_match['home_team']} vs {best_match['away_team']}",
                'hp_performance': f"{int(best_match['hp_wickets'])}/{int(best_match['hp_runs'])} in {overs} overs (Econ {econ})",
                'boundaries': f"{int(best_match['hp_dots'])} dot balls",
                'rvae_generated': round(best_match['hp_rsae'], 2),  # RSAE
                'mean_pressure_score': round(best_match['avg_pressure'], 1),
                'context_impact': 'Crucial death/pressure defense successfully choking scoring rate and breaking partnerships.'
            })

    return pd.DataFrame(case_studies)
