"""Text-based terminal interface for ciso-sim.

Run with: `python -m app.cli` or `python -m app.cli --scenario <id>`
"""
from __future__ import annotations

import argparse
import pathlib
import sys
import yaml
from typing import Dict, List

from app.services.scenario_loader import load_scenarios
from app.services.simulation import SimulationEngine
from app.config import settings


DATA_DIR = pathlib.Path(__file__).resolve().parent / "data"


def load_roster_as_raw() -> Dict[str, Dict]:
    path = DATA_DIR / "team_roster.yaml"
    with path.open("r", encoding="utf-8") as handle:
        payload = yaml.safe_load(handle)
    roster: Dict[str, Dict] = {}
    for entry in payload.get("members", []):
        roster[entry.get("id", entry.get("name"))] = entry
    return roster


def choose_scenario(scenarios: Dict[str, object], chosen: str | None) -> object:
    if chosen:
        if chosen in scenarios:
            return scenarios[chosen]
        print(f"Scenario '{chosen}' not found.")
        sys.exit(1)
    keys = list(scenarios.keys())
    print("Available scenarios:")
    for i, sid in enumerate(keys, start=1):
        s = scenarios[sid]
        print(f"{i}. {s.name} ({sid}) - {s.briefing[:60]}")
    selection = input("Choose scenario number: ").strip()
    try:
        idx = int(selection) - 1
        return scenarios[keys[idx]]
    except Exception:
        print("Invalid selection")
        sys.exit(1)


def choose_team(roster: Dict[str, Dict]) -> List[Dict]:
    # Present a numbered roster for easier selection
    items = list(roster.items())
    print("Available roster (choose by number, comma-separated):")
    for idx, (rid, r) in enumerate(items, start=1):
        print(f"{idx}. {r.get('name')} ({rid}) - {r.get('role')}")
    selection = input("Enter numbers (comma) or press Enter for default (first 3): ").strip()
    if not selection:
        # default: first 3 entries
        return [items[i][1] for i in range(min(3, len(items)))]

    parts = [s.strip() for s in selection.split(",") if s.strip()]
    chosen: List[Dict] = []
    for p in parts:
        if p.isdigit():
            idx = int(p) - 1
            if 0 <= idx < len(items):
                chosen.append(items[idx][1])
            else:
                print(f"Warning: number '{p}' out of range; skipping")
        else:
            # Fallback: allow entering an id directly
            if p in roster:
                chosen.append(roster[p])
            else:
                print(f"Warning: '{p}' not a valid number or id; skipping")

    if not chosen:
        print("No valid team selected; using default.")
        chosen = [items[i][1] for i in range(min(3, len(items)))]

    # Validate total team cost against configured team_budget
    def team_cost(members: List[Dict]) -> int:
        return sum(int(m.get("cost", 50)) for m in members)

    while True:
        total = team_cost(chosen)
        if total <= settings.team_budget:
            break
        print(f"\nWarning: selected team cost {total} exceeds budget {settings.team_budget}.")
        resp = input("Enter 'r' to reselect team, 'c' to confirm and proceed anyway: ").strip().lower()
        if resp == "c":
            break
        if resp == "r":
            return choose_team(roster)
        print("Invalid response; please type 'r' or 'c'.")

    return chosen


def print_state(state: Dict) -> None:
    print("\n--- Current State ---")
    print(f"Budget: {state.get('budget')}")
    print(f"Reputation: {state.get('reputation')}")
    print(f"Risk: {state.get('risk')}")
    print(f"Round: {state.get('current_challenge_index', '?')}")
    print("---------------------\n")


def print_fired_banner(reason: str, final_state: Dict) -> None:
    """Display ASCII banner when CISO is fired."""
    print("\n" + "=" * 70)
    print("█" * 70)
    print("║" + " " * 68 + "║")
    print("║" + "YOU HAVE BEEN FIRED AS CISO".center(68) + "║")
    print("║" + " " * 68 + "║")
    print("█" * 70)
    print("=" * 70)
    print(f"\nReason:\n{reason}")
    print(f"\nFinal State:")
    print(f"  Budget: {final_state.get('budget')}")
    print(f"  Reputation: {final_state.get('reputation')}")
    print(f"  Risk: {final_state.get('risk')}")
    print(f"  Rounds Survived: {final_state.get('current_challenge_index', '?')}")
    print("\n" + "=" * 70 + "\n")


def run_text_ui(scenario, roster_raw: Dict[str, Dict], team_members: List[Dict]) -> None:
    engine = SimulationEngine(scenario, team_members)

    finished = False
    while not finished:
        presentable = engine.current_presentable()
        print(f"\n== {presentable.get('title')} ==")
        print(presentable.get("summary", ""))
        challenge = presentable["challenges"][0]
        print(f"\n{challenge.title}\n{challenge.prompt}\n")
        for i, opt in enumerate(challenge.options, start=1):
            prob = getattr(opt, "probability", None)
            prob_str = f" (chance: {prob}%)" if prob is not None else ""
            print(f"{i}. {opt.label}{prob_str}\n   {opt.narrative}\n")

        choice = input("Choose option number (or 'q' to quit): ").strip()
        if choice.lower() in ("q", "quit", "exit"):
            print("Exiting game.")
            return
        try:
            idx = int(choice) - 1
            if idx < 0 or idx >= len(challenge.options):
                raise ValueError()
            option = challenge.options[idx]
        except Exception:
            print("Invalid choice; try again.")
            continue

        result = engine.apply_option(option.id)
        outcome_text = result.get('outcome')
        final_state = result.get("state", {})
        print(f"\nOutcome: {outcome_text}")
        print_state(final_state)
        finished = result.get("finished", False)
        
        # Check if player was fired (budget or reputation <= 0)
        if finished and (final_state.get('budget', 1) <= 0 or final_state.get('reputation', 1) <= 0):
            print_fired_banner(outcome_text, final_state)
            print("\nGame History:")
            for h in engine.state.history:
                print(f"- Stage: {h.get('stage')} | Option: {h.get('option')} -> {h.get('outcome')}")
            return

    # Normal game end (max rounds or explicit end action)
    if finished:
        print("\n=== Scenario Complete ===")
        print(f"Final Budget: {engine.state.budget}")
        print(f"Final Reputation: {engine.state.reputation}")
        print(f"Final Risk: {engine.state.risk}")
        print("\nGame History:")
        for h in engine.state.history:
            print(f"- Stage: {h.get('stage')} | Option: {h.get('option')} -> {h.get('outcome')}")


def main(argv: List[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="ciso-sim terminal interface")
    parser.add_argument("--list-scenarios", action="store_true", help="List available scenarios")
    parser.add_argument("--scenario", help="Scenario id to run")
    parser.add_argument("--auto-team", action="store_true", help="Auto-select default team (first 3)")
    args = parser.parse_args(argv)

    scenarios = load_scenarios()

    if args.list_scenarios:
        print("Available scenarios:")
        for sid, s in scenarios.items():
            print(f"- {sid}: {s.name}")
        return 0

    scenario = choose_scenario(scenarios, args.scenario)
    roster = load_roster_as_raw()
    if args.auto_team:
        team_members = [list(roster.values())[i] for i in range(min(3, len(roster)))]
    else:
        team_members = choose_team(roster)

    run_text_ui(scenario, roster, team_members)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
