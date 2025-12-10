from __future__ import annotations

import random
from dataclasses import asdict
from typing import Dict, Optional

from app.config import settings
from app.domain.models import (
    Challenge,
    Character,
    Option,
    PlayerState,
    Scenario,
    StatBlock,
    Team,
)


class SimulationEngine:
    """Mutable simulation runtime."""

    def __init__(self, scenario: Scenario, team_members: list[dict]) -> None:
        self.scenario = scenario
        self.team = self._build_team(team_members)
        self.state = PlayerState(
            budget=settings.default_budget,
            reputation=settings.base_reputation,
            risk=50,
            current_stage=scenario.starting_stage,
            current_challenge_index=0,
            team_score=self.team.team_score,
            team_totals=self.team.team_totals,
            team_size=len(self.team.members),
        )
        self.round = 0
        self.pending_injections = list(scenario.injections)
        self.active_injection: Optional[Challenge] = None

    def current_presentable(self):
        """Return the current stage or an active injection as a stage-like payload."""
        if self.active_injection:
            challenge = self.active_injection
            self._annotate_probabilities([challenge])
            return {
                "id": f"injection-{challenge.id}",
                "title": f"Injection: {challenge.title}",
                "summary": "Unplanned event disrupts your plan.",
                "challenges": [challenge],
                "is_injection": True,
            }
        stage = self.scenario.stages[self.state.current_stage]
        challenge = stage.challenges[self.state.current_challenge_index]
        self._annotate_probabilities([challenge])
        return {
            "id": stage.id,
            "title": stage.title,
            "summary": stage.summary,
            "challenges": [challenge],
            "is_injection": False,
        }
    # apply the option and return the outcome
    def apply_option(self, option_id: str) -> Dict:
        presentable = self.current_presentable()
        option = self._find_option(presentable, option_id)
        success = self._resolve_success(option)
        outcome = option.success if success else self._pick_failure(option)
        self.round += 1

        # Apply numeric deltas
        if outcome.budget_delta is not None:
            self.state.budget += outcome.budget_delta
        self.state.budget -= int(self.team.team_score * 0.1)
        
        if outcome.reputation_delta is not None:
            self.state.reputation += outcome.reputation_delta
        
        if outcome.risk_delta is not None:
            self.state.risk = max(0, min(100, self.state.risk + outcome.risk_delta))
        
        finished = False

        self.state.history.append(
            {
                "stage": presentable["id"],
                "challenge": option.id,
                "option": option.label,
                "outcome": outcome.description,
            }
        )

        # Handle special actions
        if outcome.action:
            if outcome.action == "end":
                finished = True
            else:
                self._execute_action(outcome.action)

        if presentable.get("is_injection"):
            self.active_injection = None
        else:
            stage = self.scenario.stages[self.state.current_stage]
            is_last = self.state.current_challenge_index >= len(stage.challenges) - 1
            if is_last:
                if outcome.next_stage:
                    self.state.current_stage = outcome.next_stage
                    self.state.current_challenge_index = 0
                else:
                    finished = True
            else:
                # Advance within the current stage; defer stage transition until the last challenge.
                self.state.current_challenge_index += 1

        # Randomly surface an injection if available and none active (weighted by injection weight, risk-aware trigger).
        if not presentable.get("is_injection") and self.pending_injections:
            chance = settings.injection_base_chance + (
                self.state.risk * settings.injection_risk_factor
            )
            chance = min(chance, settings.injection_max_chance)
            if random.random() < chance:
                weights = [inj.weight for inj in self.pending_injections]
                chosen = random.choices(self.pending_injections, weights=weights, k=1)[0]
                self.pending_injections.remove(chosen)
                self.active_injection = chosen

        if not presentable.get("is_injection"):
            finished = finished or self.round >= settings.max_rounds
        return {
            "state": asdict(self.state),
            "round": self.round,
            "finished": finished,
            "outcome": outcome.description,
            "success": success,
        }

    def _execute_action(self, action: str) -> None:
        """Execute special actions triggered by outcomes."""
        if action == "remove-member":
            # Remove a random team member
            if self.team.members:
                removed = self.team.members.pop(0)
                self.state.team_size = len(self.team.members)
                self._recalculate_team_stats()
        elif action == "reset-team":
            # Reset all team members' mental state (could represent stress recovery)
            # In future, could tie to team morale or stress metrics
            pass
        elif action == "boost-morale":
            # Improve team morale/cohesion
            self.team.team_score = min(100, self.team.team_score + 10)
        elif action == "damage-morale":
            # Reduce team morale/cohesion
            self.team.team_score = max(0, self.team.team_score - 10)
        elif action == "double-budget":
            # Grant emergency budget
            self.state.budget += settings.default_budget // 2
        elif action == "burn-budget":
            # Emergency expenditure
            self.state.budget = max(0, self.state.budget - settings.default_budget // 2)

    def _recalculate_team_stats(self) -> None:
        """Recalculate team totals after team composition changes."""
        totals = {
            "analysis": sum(m.stats.analysis for m in self.team.members) if self.team.members else 0,
            "comms": sum(m.stats.comms for m in self.team.members) if self.team.members else 0,
            "engineering": sum(m.stats.engineering for m in self.team.members) if self.team.members else 0,
            "leadership": sum(m.stats.leadership for m in self.team.members) if self.team.members else 0,
        }
        self.team.team_totals = totals
        self.state.team_totals = totals
        self.team.team_score = int(sum(totals.values()) / (4 * max(1, len(self.team.members))))
        self.state.team_score = self.team.team_score

    def _find_option(self, presentable, option_id: str) -> Option:
        for challenge in presentable["challenges"]:
            for option in challenge.options:
                if option.id == option_id:
                    return option
        raise ValueError(f"Option {option_id} not found in stage {presentable['id']}")

    def _resolve_success(self, option: Option) -> bool:
        chance = self._compute_chance(option)
        return random.random() < chance

    def _pick_failure(self, option: Option):
        if option.failure:
            return option.failure
        # derive a default failure if not provided
        return type(option.success)(
            description=f"Failed: {option.success.description}",
            budget_delta=int(-abs(option.success.budget_delta) or -2),
            reputation_delta=int(-abs(option.success.reputation_delta) or -2),
            risk_delta=abs(option.success.risk_delta) + 2,
            next_stage=option.success.next_stage,
        )

    def _compute_chance(self, option: Option) -> float:
        stat_total = self.team.team_totals.get(option.skill, self.team.team_score)
        base = 0.5
        delta = (stat_total - option.difficulty) / 200
        return min(0.95, max(0.05, base + delta))

    def _annotate_probabilities(self, challenges):
        for challenge in challenges:
            for opt in challenge.options:
                opt.probability = round(self._compute_chance(opt) * 100)

    def _build_team(self, raw_members: list[dict]) -> Team:
        members: list[Character] = []
        for entry in raw_members:
            stats = entry.get("stats", {}) if isinstance(entry, dict) else {}
            members.append(
                Character(
                    name=entry.get("name", "Analyst"),
                    role=entry.get("role", "Analyst"),
                    cost=int(entry.get("cost", 50)),
                    stats=StatBlock(
                        analysis=int(stats.get("analysis", 50)),
                        comms=int(stats.get("comms", 50)),
                        engineering=int(stats.get("engineering", 50)),
                        leadership=int(stats.get("leadership", 50)),
                    ),
                )
            )
        # Compute team totals and aggregate score.
        totals = {
            "analysis": sum(m.stats.analysis for m in members) if members else 0,
            "comms": sum(m.stats.comms for m in members) if members else 0,
            "engineering": sum(m.stats.engineering for m in members) if members else 0,
            "leadership": sum(m.stats.leadership for m in members) if members else 0,
        }
        team_score = int(sum(totals.values()) / (4 * max(1, len(members))))
        team = Team(members=members)
        team.team_totals = totals  # type: ignore[attr-defined]
        team.team_score = team_score  # type: ignore[attr-defined]
        return team


class SimulationRegistry:
    """In-memory store for active games (swap with DB/cache later)."""

    def __init__(self) -> None:
        self._games: Dict[str, SimulationEngine] = {}

    def create(self, game_id: str, scenario: Scenario, team_members: list[dict]) -> SimulationEngine:
        engine = SimulationEngine(scenario, team_members)
        self._games[game_id] = engine
        return engine

    def get(self, game_id: str) -> Optional[SimulationEngine]:
        return self._games.get(game_id)

    def delete(self, game_id: str) -> None:
        self._games.pop(game_id, None)

