"""
Future Pressure Analysis Architecture Module (Stage 2 Specification).
Prepares extensible data models, mathematical formulations, and interface contracts
for calculating the Pressure Performance Index (PPI) in Round 1 of SupeRR Selector Season 2.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Optional
import pandas as pd
import numpy as np


class PressureTier(Enum):
    LOW = "Low"
    MODERATE = "Moderate"
    HIGH = "High"
    EXTREME = "Extreme"


@dataclass
class MatchSituationVector:
    """
    Delivery-level or over-level situational vector used to quantify pressure.
    """
    innings: int
    balls_remaining: int
    wickets_remaining: int
    current_run_rate: float
    required_run_rate: Optional[float]
    target: Optional[int]
    runs_required: Optional[int]
    innings_stage: str  # 'Powerplay', 'Middle', 'Death'
    is_knockout: bool


class PressureIndexArchitect:
    """
    Blueprint for Stage 2 Pressure Scoring & Ranking Engine.
    Kept modularly decoupled from the Stage 1 statistics engine.
    """

    @staticmethod
    def classify_innings_stage(legal_balls_bowled: int) -> str:
        """
        Classifies standard 20-over T20 innings stage based on legal balls bowled.
        - Powerplay: overs 1-6 (balls 1 to 36)
        - Middle: overs 7-15 (balls 37 to 90)
        - Death: overs 16-20 (balls 91 to 120)
        """
        if legal_balls_bowled <= 36:
            return "Powerplay"
        elif legal_balls_bowled <= 90:
            return "Middle"
        else:
            return "Death"

    @staticmethod
    def calculate_situational_pressure_index(situation: MatchSituationVector) -> float:
        """
        Calculates an objective continuous Pressure Score [0.0 to 10.0] for a match situation.
        
        Mathematical Formulation:
        1. Innings 1 (Setting the Target):
           Pressure is a function of:
           - Wickets lost early in the innings (collapse pressure)
           - Death overs acceleration necessity
           - Tournament stakes (knockout vs league match)
           
        2. Innings 2 (Chasing the Target):
           Pressure is primarily driven by Required Run Rate (RRR) relative to par:
           - RRR vs balls remaining elasticity
           - Resource deficit (Duckworth-Lewis-Stern style wickets-in-hand penalty)
           - Stage of chase (Death overs chasing > Middle overs)
        """
        if situation.innings == 1:
            stage_weight = 1.0 if situation.innings_stage == "Powerplay" else (1.2 if situation.innings_stage == "Middle" else 1.8)
            resource_strain = max(0.0, (10 - situation.wickets_remaining) * 0.4)
            base_pressure = 2.0 + resource_strain * stage_weight
            if situation.is_knockout:
                base_pressure *= 1.25
            return min(10.0, round(base_pressure, 2))
        else:
            # Innings 2 (Chase)
            rrr = situation.required_run_rate or 8.0
            wickets_left = situation.wickets_remaining
            balls_left = situation.balls_remaining
            
            # Non-linear pressure escalation as RRR rises and wickets fall
            rate_pressure = max(0.0, (rrr - 7.5) * 0.75)
            resource_penalty = max(0.0, (10 - wickets_left) / 2.0)
            urgency = (120 - balls_left) / 120.0
            
            score = 3.0 + rate_pressure + (resource_penalty * urgency)
            if situation.is_knockout:
                score *= 1.2
            return min(10.0, round(max(1.0, score), 2))

    @staticmethod
    def apply_empirical_bayes_shrinkage(
        observed_metric: float,
        population_mean: float,
        sample_size: int,
        k_threshold: int = 50
    ) -> float:
        """
        Applies empirical Bayes shrinkage to prevent sample-size distortions.
        Adjusts extreme performances over small sample sizes towards population baseline.
        
        Formula:
        Adjusted = (n / (n + k)) * Observed + (k / (n + k)) * Population_Baseline
        """
        weight = sample_size / (sample_size + k_threshold)
        shrunk_metric = (weight * observed_metric) + ((1.0 - weight) * population_mean)
        return round(shrunk_metric, 2)
