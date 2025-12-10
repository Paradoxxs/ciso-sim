from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class Outcome:
    """Resulting impacts for a branch (success or failure)."""

    description: str
    budget_delta: Optional[int] = None
    reputation_delta: Optional[int] = None
    risk_delta: Optional[int] = None
    next_stage: Optional[str] = None
    action: Optional[str] = None  # Special actions: end, remove-member, reset-team, boost-morale, etc.


@dataclass
class Option:
    """A decision the player can make for a challenge."""

    id: str
    label: str
    narrative: str
    success: Outcome
    failure: Optional[Outcome] = None
    difficulty: int = 100  # baseline 0-100; higher = harder
    skill: str = "analysis"  # which team ability applies
    action: str = "continue"  # continue, end, or next_stage


@dataclass
class Challenge:
    """Single decision point presented to the player."""

    id: str
    title: str
    prompt: str
    options: List[Option] = field(default_factory=list)


@dataclass
class Injection:
    """Unplanned event that can occur mid-scenario."""

    id: str
    title: str
    prompt: str
    weight: int = 5
    options: List[Option] = field(default_factory=list)


@dataclass
class Stage:
    """Phase of the scenario (e.g., detection, containment)."""

    id: str
    title: str
    summary: str
    challenges: List[Challenge] = field(default_factory=list)


@dataclass
class Scenario:
    """Top level game definition."""

    id: str
    name: str
    briefing: str
    stages: Dict[str, Stage]
    starting_stage: str
    injections: List[Injection] = field(default_factory=list)


@dataclass
class PlayerState:
    """Mutable state tracked through a run."""

    budget: int
    reputation: int
    risk: int
    current_stage: str
    current_challenge_index: int = 0
    history: List[Dict[str, str]] = field(default_factory=list)
    team_score: int = 50
    team_totals: Dict[str, int] = field(default_factory=dict)
    team_size: int = 0


@dataclass
class StatBlock:
    """Skill stats for a character (0-100 scale)."""

    analysis: int
    comms: int
    engineering: int
    leadership: int


@dataclass
class Character:
    """Single team member."""

    name: str
    role: str
    cost: int
    stats: StatBlock


@dataclass
class Team:
    """Security team roster."""

    members: List[Character] = field(default_factory=list)
    team_totals: Dict[str, int] = field(default_factory=dict)
    team_score: int = 50

