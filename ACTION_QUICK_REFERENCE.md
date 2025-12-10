# Action System Quick Reference

## Quick Start: Adding Actions to Outcomes

### Basic Pattern
```yaml
outcome:
  description: What happened
  action: action_name
  budget_delta: 0
  reputation_delta: 0
  risk_delta: 0
```

### Action-Only Pattern (no stat changes)
```yaml
outcome:
  description: What happened
  action: end
```

## All Available Actions

### 1. **end** - End Scenario
Immediately ends the scenario and marks it as finished.
```yaml
action: end
```

### 2. **remove-member** - Remove Team Member  
Removes first team member and recalculates all team stats.
```yaml
action: remove-member
budget_delta: -5      # Cost of replacement
reputation_delta: -1  # Impact of losing member
```

### 3. **boost-morale** - Improve Team Score
Increases team score by 10 (max 100). Makes future decisions easier.
```yaml
action: boost-morale
reputation_delta: -2  # Cost of break time
budget_delta: -5
```

### 4. **damage-morale** - Decrease Team Score
Decreases team score by 10 (min 0). Makes future decisions harder.
```yaml
action: damage-morale
reputation_delta: 1   # Shows commitment
risk_delta: 5
```

### 5. **double-budget** - Grant Emergency Funds
Adds 50 to budget (50% of default 100).
```yaml
action: double-budget
reputation_delta: 2
```

### 6. **burn-budget** - Emergency Expenditure
Subtracts 50 from budget (50% of default 100).
```yaml
action: burn-budget
reputation_delta: 3
budget_delta: -10
```

### 7. **reset-team** - Placeholder
Reserved for future team status effects.

## Real Examples from injections.yaml

### End Scenario Example
```yaml
- id: false-alarm
  title: False alarm
  prompt: It was a penetration test!
  options:
    - id: end-scenario
      label: End the scenario
      narrative: It was just an external pen test the CEO hired.
      outcome:
        description: End the scenario
        action: end
```

### Remove Member Example
```yaml
- id: food-poisoning
  title: Food poisoning
  prompt: One of your team members goes to the hospital.
  options:
    - id: loss-of-staff
      label: Loss of staff
      narrative: One team member ate something bad.
      outcome:
        description: Say goodbye to one team member.
        action: remove-member
```

### Boost Morale Example
```yaml
- id: team-burnout
  title: Team morale hits rock bottom
  prompt: Your team is exhausted from constant incident response.
  options:
    - id: give-break
      label: Give the team a weekend off
      narrative: Send everyone home to recover mentally.
      outcome:
        description: The team returns refreshed and ready.
        action: boost-morale
        reputation_delta: -2
        budget_delta: -5
        risk_delta: -3
```

### Multiple Options with Different Actions
```yaml
- id: emergency-funding
  title: Emergency funding becomes available
  prompt: The board has approved emergency incident response funding.
  options:
    - id: accept-funds
      label: Accept the budget injection
      outcome:
        description: Additional budget available.
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

## Implementation Notes

### How Actions Execute
1. Outcome is determined (success or failure)
2. Numeric deltas applied (if present)
3. Action executed (if present)
4. Game state continues

### Team Stats When Member Removed
```
New team_score = sum(all_skill_totals) / (4 * team_size)
Example: 4 members with 60 avg each
  = (240 + 240 + 240 + 240) / (4 * 4)
  = 960 / 16 = 60

After removing 1 member:
  = (180 + 180 + 180 + 180) / (4 * 3)
  = 720 / 12 = 60
```

### Stat Bounds
- **Team Score**: 0-100
- **Budget**: 0+ (capped by game logic at 0 minimum)
- **Reputation**: No hard caps (but typically 0-100)
- **Risk**: 0-100 (enforced by risk_delta application)

## Testing Actions

### Load and verify
```python
from app.services.scenario_loader import load_scenarios

scenarios = load_scenarios()
scenario = next(iter(scenarios.values()))

for inj in scenario.injections:
    for opt in inj.options:
        if opt.success.action:
            print(f"{inj.title}: {opt.success.action}")
```

### Run simulation with actions
```python
from app.services.simulation import SimulationEngine

engine = SimulationEngine(scenario, team_members)
# Engine now has action support
# _execute_action() will run when options are chosen
```

## Files Using Actions

- **Define**: `app/data/injections.yaml` - Global injections with actions
- **Define**: Scenario YAML files - Scenario-specific injections
- **Load**: `app/services/scenario_loader.py` - Loads action from YAML
- **Model**: `app/domain/models.py` - Outcome.action field
- **Execute**: `app/services/simulation.py` - Runs actions and recalculates stats
- **Documentation**: `ACTION_SYSTEM.md` - Full system documentation

## Future Actions Ideas

- `skip-next-challenge` - Skip next challenge in stage
- `add-member` - Add new team member
- `unlock-member` - Unlock team member for hiring
- `apply-tool` - Grant new capability
- `damage-reputation` - Board escalation risk
- `reset-risk` - Drop risk to baseline
- `critical-alert` - Force risk increase
- `media-coverage` - Positive/negative press

---
For complete documentation, see: **ACTION_SYSTEM.md**
