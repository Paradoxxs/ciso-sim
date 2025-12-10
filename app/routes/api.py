from __future__ import annotations

import uuid
from dataclasses import asdict
from typing import Dict

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.config import settings
from app.services.scenario_loader import load_scenarios
from app.services.simulation import SimulationRegistry
from app.services.team_loader import load_roster

router = APIRouter(prefix="/api")
registry = SimulationRegistry()
scenarios = load_scenarios()
roster = load_roster()
roster_map = {member.name: member for member in roster}


class CreateSessionPayload(BaseModel):
    scenario_id: str
    team: list[dict] = Field(
        default_factory=list,
        description="List of characters with stats. Example: [{name, role, stats:{analysis, comms, engineering, leadership}}]",
    )


@router.get("/roster")
async def list_roster():
    return {
        "budget": settings.team_budget,
        "members": [
            {
                "id": member.name,
                "name": member.name,
                "role": member.role,
                "cost": member.cost,
                "stats": {
                    "analysis": member.stats.analysis,
                    "comms": member.stats.comms,
                    "engineering": member.stats.engineering,
                    "leadership": member.stats.leadership,
                },
            }
            for member in roster
        ],
    }


class DecisionPayload(BaseModel):
    option_id: str


def serialize_stage(stage_payload) -> Dict:
    return {
        "id": stage_payload["id"],
        "title": stage_payload["title"],
        "summary": stage_payload["summary"],
        "is_injection": stage_payload.get("is_injection", False),
        "challenges": [
            {
                "id": challenge.id,
                "title": challenge.title,
                "prompt": challenge.prompt,
                "options": [
                    {
                        "id": option.id,
                        "label": option.label,
                        "narrative": option.narrative,
                        "skill": option.skill,
                        "difficulty": option.difficulty,
                        "probability": getattr(option, "probability", None),
                    }
                    for option in challenge.options
                ],
            }
            for challenge in stage_payload["challenges"]
        ],
    }


@router.get("/scenarios")
async def list_scenarios():
    return [
        {
            "id": scenario.id,
            "name": scenario.name,
            "briefing": scenario.briefing,
        }
        for scenario in scenarios.values()
    ]


@router.post("/session")
async def create_session(payload: CreateSessionPayload):
    scenario = scenarios.get(payload.scenario_id)
    if not scenario:
        raise HTTPException(status_code=404, detail="Scenario not found")

    # Build team from roster (server-authoritative) and enforce cost budget
    validated_team = []
    total_cost = 0
    for entry in payload.team:
        name = entry.get("name")
        member = roster_map.get(name)
        if not member:
            continue
        total_cost += member.cost
        validated_team.append(
            {
                "name": member.name,
                "role": member.role,
                "cost": member.cost,
                "stats": {
                    "analysis": member.stats.analysis,
                    "comms": member.stats.comms,
                    "engineering": member.stats.engineering,
                    "leadership": member.stats.leadership,
                },
            }
        )

    if total_cost > settings.team_budget:
        raise HTTPException(
            status_code=400,
            detail=f"Team over budget: {total_cost} > {settings.team_budget}",
        )

    session_id = uuid.uuid4().hex
    engine = registry.create(session_id, scenario, validated_team)
    stage = engine.current_presentable()
    return {
        "session_id": session_id,
        "state": asdict(engine.state),
        "stage": serialize_stage(stage),
    }


@router.post("/session/{session_id}/decision")
async def submit_decision(session_id: str, payload: DecisionPayload):
    engine = registry.get(session_id)
    if not engine:
        raise HTTPException(status_code=404, detail="Session not found")

    result = engine.apply_option(payload.option_id)
    if not result["finished"]:
        result["stage"] = serialize_stage(engine.current_presentable())
    else:
        registry.delete(session_id)
        result["stage"] = None
    return result

