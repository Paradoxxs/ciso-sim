# Cybersecurity Leader Simulation

Python-first web app inspired by SANS Cyber42 tabletop exercises. Run a scenario as the acting CISO, make trade-offs, and watch how budget, reputation, and risk evolve.

## Stack
- FastAPI + Uvicorn for API & server-side rendering
- Jinja2 templates + vanilla JS for lightweight UI
- YAML-driven scenario definitions

## Getting Started
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Visit `http://127.0.0.1:8000` and launch a scenario.

## Project Structure
```
app/
  config.py              # Simulation defaults
  domain/models.py       # Dataclasses for scenario graph
  services/              # Scenario loader + simulation engine
  routes/                # API + UI routers
  templates/             # Jinja2 templates
  static/                # CSS and JS assets
  data/                  # YAML content packs
docs/
  architecture.md        # Design overview and roadmap hooks
```

## Next Ideas
- Persist sessions in Redis/Postgres for multi-user facilitation.
- Add facilitator dashboard with timeline playback.
- Generate scoring badges for leadership competencies.

## Terminal (text) version

A simple text-based interface is available to run scenarios from the terminal (no web UI required).

Activate your Python environment and run:

```powershell
python -m app.cli --list-scenarios
python -m app.cli --scenario <scenario_id>
```

Use `--auto-team` to select a default team automatically. When run interactively the CLI will prompt you to choose a scenario and team members.

