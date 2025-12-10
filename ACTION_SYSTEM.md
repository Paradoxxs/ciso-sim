# Action System Documentation

## Overview

The action system allows outcomes in scenarios and global injections to trigger special game effects beyond simple stat adjustments (budget, reputation, risk). Actions enable scenario designers to create dynamic, consequential decision points that change the game state in meaningful ways.

## Supported Actions

### 1. `end`
**Description:** Immediately ends the scenario and marks the game as finished.

**Use Case:** When a decision resolves the entire incident (e.g., finding that a security breach was a false alarm).

**YAML Example:**
```yaml
outcome:
  description: End the scenario
  action: end
```

### 2. `remove-member`
**Description:** Removes the first team member from the active team and recalculates all team statistics.

**Impact:**
- Reduces team size by 1
- Recalculates team skill totals (analysis, comms, engineering, leadership)
- Recalculates team score (average of all skill totals divided by number of members)
- Updates `state.team_totals` and `state.team_score` accordingly

**Use Case:** When a team member leaves the team due to illness, departure, or incident consequences.

**YAML Example:**
```yaml
outcome:
  description: Say goodbye to one of the team members.
  action: remove-member
  budget_delta: 0
  reputation_delta: -1
  risk_delta: 2
```

### 3. `boost-morale`
**Description:** Increases team morale by 10 points (capped at 100).

**Impact:**
- Raises `team.team_score` by 10 (minimum 100)
- Makes future decisions easier (higher team score = higher success chance)
- Does not affect individual member statistics

**Use Case:** When the team receives praise, recognition, or a well-deserved break.

**YAML Example:**
```yaml
outcome:
  description: The team returns refreshed and ready.
  action: boost-morale
  reputation_delta: -2
  budget_delta: -5
```

### 4. `damage-morale`
**Description:** Decreases team morale by 10 points (floored at 0).

**Impact:**
- Lowers `team.team_score` by 10 (minimum 0)
- Makes future decisions harder (lower team score = lower success chance)
- Does not affect individual member statistics

**Use Case:** When the team faces setbacks, criticism, or exhaustion.

**YAML Example:**
```yaml
outcome:
  description: Team suffers more burnout but shows commitment.
  action: damage-morale
  reputation_delta: 1
  risk_delta: 5
```

### 5. `double-budget`
**Description:** Grants emergency budget equal to 50% of the default budget.

**Impact:**
- Adds `default_budget // 2` to `state.budget`
- Default budget typically 100, so adds 50 points

**Use Case:** Emergency funding approval, board support, or unexpected resource allocation.

**YAML Example:**
```yaml
outcome:
  description: Additional budget available for response efforts.
  action: double-budget
  reputation_delta: 2
```

### 6. `burn-budget`
**Description:** Removes emergency budget equal to 50% of the default budget.

**Impact:**
- Subtracts `default_budget // 2` from `state.budget` (floored at 0)
- Default budget typically 100, so removes 50 points

**Use Case:** Emergency expenditure, financial penalties, or resource reallocation to other departments.

**YAML Example:**
```yaml
outcome:
  description: Board respects the restraint.
  action: burn-budget
  reputation_delta: 3
  budget_delta: -10
```

### 7. `reset-team`
**Description:** Resets team mental state (currently a placeholder for future expansion).

**Impact:** Currently has no effect but reserved for future team-specific status effects.

**Use Case:** Placeholder for team morale recovery systems or stress reduction.

## Implementation Details

### How Actions Execute

1. When an option is chosen, the outcome is determined (success or failure)
2. Stat deltas (budget, reputation, risk) are applied
3. If the outcome has an `action` field, it is executed
4. Special handling for `end` action: sets `finished=True` to end the scenario

### Action Processing Order

```
1. Determine outcome (success/failure)
2. Apply numeric deltas (budget, reputation, risk)
3. Record decision history
4. Execute action if present
5. Advance scenario state
6. Check for random injection trigger
```

### Team Stats Recalculation

When a team member is removed via `remove-member`:

```python
totals = {
    "analysis": sum(member.stats.analysis for member in team.members),
    "comms": sum(member.stats.comms for member in team.members),
    "engineering": sum(member.stats.engineering for member in team.members),
    "leadership": sum(member.stats.leadership for member in team.members),
}
team_score = sum(totals.values()) / (4 * len(team.members))
```

## Example YAML Definitions

### Simple Action (End Scenario)
```yaml
- id: false-alarm
  title: False alarm
  prompt: It was a penetration test!
  options:
    - id: end-scenario
      label: End the scenario
      narrative: It was just a penetration test the CEO hired.
      outcome:
        description: End the scenario
        action: end
```

### Combined Stats + Action
```yaml
- id: team-burnout
  title: Team morale hits rock bottom
  prompt: Your team is exhausted from constant incident response.
  options:
    - id: give-break
      label: Give the team a weekend off
      narrative: Send everyone home for the weekend to recover.
      outcome:
        description: The team returns refreshed and ready.
        action: boost-morale
        reputation_delta: -2
        budget_delta: -5
        risk_delta: -3
```

### Multiple Actions in Different Options
```yaml
- id: emergency-funding
  title: Emergency funding becomes available
  prompt: The board has approved emergency incident response funding.
  options:
    - id: accept-funds
      label: Accept the emergency budget injection
      outcome:
        description: Additional budget available for response efforts.
        action: double-budget
        reputation_delta: 2
    - id: decline-funds
      label: Maintain fiscal discipline
      outcome:
        description: Board respects the restraint.
        action: burn-budget
        reputation_delta: 3
        budget_delta: -10
```

## Future Action Types

Potential actions for future implementation:

- `skip-next-challenge`: Skip the next challenge in the stage
- `add-member`: Add a new team member to the roster
- `damage-reputation`: Increase risk of board escalation
- `inject-specific`: Force a specific injection to appear
- `unlock-team-member`: Unlock a new team member for hiring
- `apply-tool`: Provide a new capability/tool to the team
- `trigger-compliance-violation`: Incur compliance penalties
- `positive-media`: Gain positive media coverage

## Testing Action Execution

To test actions in development:

```python
from app.services.simulation import SimulationEngine
from app.services.scenario_loader import load_scenarios

scenarios = load_scenarios()
scenario = next(iter(scenarios.values()))
team = [{"name": "Test", "role": "Analyst", "cost": 50, ...}]

engine = SimulationEngine(scenario, team)
# Apply an option with an action
result = engine.apply_option(option_id)
# Check state changes for action effects
print(engine.state.team_size)  # For remove-member
print(engine.team.team_score)  # For boost/damage-morale
print(engine.state.budget)     # For double/burn-budget
```

## Best Practices

1. **Combine Stats with Actions**: Use both deltas and actions together for compound effects
   ```yaml
   action: remove-member
   budget_delta: -5  # Cost of replacing the member
   reputation_delta: -2  # Impact of losing capability
   ```

2. **Make Actions Consequential**: Ensure actions represent meaningful game state changes
3. **Balance Outcomes**: Provide alternative paths where players can avoid or mitigate action consequences
4. **Use Weighted Injections**: Set injection weights to control how often actions appear
5. **Document Custom Actions**: Add comments to explain why specific actions are chosen

## Related Files

- `app/domain/models.py` - Outcome dataclass with action field
- `app/services/scenario_loader.py` - Loads actions from YAML
- `app/services/simulation.py` - Executes actions via `_execute_action()` and `_recalculate_team_stats()`
- `app/data/injections.yaml` - Examples of global injections with actions
