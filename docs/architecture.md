# Cybersecurity Leader Simulation - Architecture

## Goals
- Deliver a browser-based leadership simulation inspired by SANS Cyber42.
- Keep the entire stack Python-native for maintainability.
- Provide space for rich scenario content and future analytics.

## High-Level Overview
| Layer | Components | Responsibility |
| --- | --- | --- |
| Presentation | FastAPI + Jinja2 templates, `app/static/app.js` | Render scenario selector, fetch API responses, interactively update UI without page reloads. |
| API | `app/routes/api.py` | Manage sessions, expose scenario metadata, evaluate decisions. |
| Domain | `app/domain/models.py` | Typed dataclasses describing Scenarios, Stages, Challenges, Options, PlayerState. |
| Services | `app/services/scenario_loader.py`, `simulation.py` | Load YAML scenarios, apply decision logic, track history. |
| Data | `app/data/*.yaml` | Content packs for exercises. |

## Request Flow
1. Player loads `/` handled by `app/routes/ui.py`. Template renders selector and static assets.
2. Front-end script POSTs `/api/session` with `scenario_id`.
3. API builds `SimulationEngine`, seeded with defaults from `app/config.py`.
4. Player choices POST to `/api/session/{session}/decision`. Engine mutates `PlayerState`, returns updated metrics and optionally next stage payload.
5. When rounds exceed `SimulationSettings.max_rounds` or stage chain ends, the engine flags completion and session is removed from the registry.

## Extensibility Points
- Swap `SimulationRegistry` with Redis or Postgres when persistence is required.
- Enrich `Outcome` to include compliance, legal, or workforce metrics.
- Introduce scoring models in `simulation.py` that unlock achievements or endings.
- Add authentication middleware for multi-user facilitation.

## Local Development
```bash
pip install -r requirements.txt
uvicorn app.main:app --reload
```

