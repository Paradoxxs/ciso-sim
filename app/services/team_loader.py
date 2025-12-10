from __future__ import annotations

import pathlib
from typing import Dict, List

import yaml

from app.domain.models import Character, StatBlock

DATA_DIR = pathlib.Path(__file__).resolve().parent.parent / "data"


def load_roster() -> List[Character]:
    path = DATA_DIR / "team_roster.yaml"
    with path.open("r", encoding="utf-8") as handle:
        payload = yaml.safe_load(handle)
    members = []
    for entry in payload.get("members", []):
        stats = entry.get("stats", {})
        members.append(
            Character(
                name=entry["name"],
                role=entry["role"],
                cost=int(entry.get("cost", 50)),
                stats=StatBlock(
                    analysis=int(stats.get("analysis", 50)),
                    comms=int(stats.get("comms", 50)),
                    engineering=int(stats.get("engineering", 50)),
                    leadership=int(stats.get("leadership", 50)),
                ),
            )
        )
    return members


def select_team(member_ids: List[str], roster: Dict[str, Dict]) -> List[Dict]:
    selected = []
    for member_id in member_ids:
        if member_id not in roster:
            continue
        selected.append(roster[member_id])
    return selected

