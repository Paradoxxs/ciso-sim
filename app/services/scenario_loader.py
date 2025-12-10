from __future__ import annotations

import pathlib
from typing import Dict

import yaml

from app.domain.models import (
    Challenge,
    Injection,
    Option,
    Outcome,
    Scenario,
    Stage,
)

DATA_DIR = pathlib.Path(__file__).resolve().parent.parent / "data"


def _load_global_injections() -> Dict[str, Injection]:
    """Load global injections from injections.yaml that apply to all scenarios."""
    injections_path = DATA_DIR / "injections.yaml"
    if not injections_path.exists():
        return {}
    
    with injections_path.open("r", encoding="utf-8") as handle:
        payload = yaml.safe_load(handle)
    
    if not payload or "injections" not in payload:
        return {}
    
    global_injections = {}
    for injection_payload in payload["injections"]:
        injection = _build_injection(injection_payload)
        global_injections[injection.id] = injection
    
    return global_injections


def load_scenarios() -> Dict[str, Scenario]:
    """Load all scenario definitions from YAML files (skips non-scenario YAML like roster)."""
    global_injections = _load_global_injections()
    scenarios: Dict[str, Scenario] = {}
    for yaml_path in DATA_DIR.glob("*.yaml"):
        with yaml_path.open("r", encoding="utf-8") as handle:
            payload = yaml.safe_load(handle)
        if not payload or "stages" not in payload:
            continue
        scenario = _build_scenario(payload, global_injections)
        scenarios[scenario.id] = scenario
    return scenarios


def _build_scenario(payload: Dict, global_injections: Dict[str, Injection]) -> Scenario:
    stages = {}
    for stage_payload in payload["stages"]:
        stage = Stage(
            id=stage_payload["id"],
            title=stage_payload["title"],
            summary=stage_payload["summary"],
            challenges=[
                _build_challenge(challenge_payload)
                for challenge_payload in stage_payload["challenges"]
            ],
        )
        stages[stage.id] = stage

    # Build scenario-specific injections
    scenario_injections = [
        _build_injection(injection_payload)
        for injection_payload in payload.get("injections", [])
    ]
    
    # Combine global and scenario-specific injections
    all_injections = list(global_injections.values()) + scenario_injections

    return Scenario(
        id=payload["id"],
        name=payload["name"],
        briefing=payload["briefing"],
        stages=stages,
        starting_stage=payload["starting_stage"],
        injections=all_injections,
    )


def _build_challenge(payload: Dict) -> Challenge:
    return Challenge(
        id=payload["id"],
        title=payload["title"],
        prompt=payload["prompt"],
        options=[
            Option(
                id=option_payload["id"],
                label=option_payload["label"],
                narrative=option_payload["narrative"],
                success=_build_outcome(option_payload["outcome"]),
                failure=_build_outcome(option_payload.get("failure")) if option_payload.get("failure") else None,
                difficulty=option_payload.get("difficulty", 100),
                skill=option_payload.get("skill", "analysis"),
            )
            for option_payload in payload["options"]
        ],
    )


def _build_injection(payload: Dict) -> Injection:
    return Injection(
        id=payload["id"],
        title=payload["title"],
        prompt=payload["prompt"],
        weight=payload.get("weight", 5),
        options=[
            Option(
                id=option_payload["id"],
                label=option_payload["label"],
                narrative=option_payload["narrative"],
                success=_build_outcome(option_payload["outcome"]),
                failure=_build_outcome(option_payload.get("failure")) if option_payload.get("failure") else None,
                difficulty=option_payload.get("difficulty", 50),
                skill=option_payload.get("skill", "analysis"),
            )
            for option_payload in payload["options"]
        ],
    )


def _build_outcome(payload: Dict) -> Outcome:
    return Outcome(
        description=payload["description"],
        budget_delta=payload.get("budget_delta"),
        reputation_delta=payload.get("reputation_delta"),
        risk_delta=payload.get("risk_delta"),
        next_stage=payload.get("next_stage"),
        action=payload.get("action"),
    )

