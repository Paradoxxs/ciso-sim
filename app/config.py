from pydantic import BaseModel


class SimulationSettings(BaseModel):
    """Runtime configuration for the simulation engine."""

    max_rounds: int = 10
    default_budget: int = 100
    base_reputation: int = 70
    injection_base_chance: float = 0.15
    injection_risk_factor: float = 0.005
    injection_max_chance: float = 0.7
    team_budget: int = 200


settings = SimulationSettings()

