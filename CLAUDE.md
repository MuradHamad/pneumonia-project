# CLAUDE.md

Instructions for Claude Code working on this project. Read this file first on every session.

---

## Project

**Multi-Modal AI System for Pneumonia Severity Assessment**
Graduation Project (GP2) — University of Petra, Software Engineering
Author: Murad Hamad

A web application where clinicians upload chest X-rays + clinical data, an AI fusion model returns a severity score and risk class with a heatmap, and reports can be generated and exported.

---

## Stack (locked, do not change)

- **Backend:** Django 5.x (Python 3.11+)
- **Database:** SQLite
- **Frontend:** Django templates + Tailwind CSS (CDN, no build step)
- **AI model:** PyTorch, trained separately in Colab, plugged in as `.pt` file
- **Auth:** Django's built-in auth (AbstractUser)

Do not suggest Next.js, React, FastAPI, PostgreSQL, or any other replacement. These were deliberately chosen.

---

## Documentation (source of truth)

Always read these before making design decisions:

- `docs/schema.md` — database schema, every table, every constraint
- `docs/ui-design.md` — pages, components, colors, layout
- `docs/phases.md` — build order
- `docs/diagrams/` — UML diagrams (class, use case, 4 sequence diagrams)

**If the code ever conflicts with the diagrams or schema, the diagrams win. Ask before diverging.**

---

## Architectural principles

1. **MVC strictly.** Models in `models.py`, views in `views.py`, templates in `templates/`. No business logic in templates.
2. **Services are stateless.** `FusionModel` and `ChatBot` live in `services/` as plain Python classes/modules. They are NOT Django models and have NO database tables.
3. **Composition matters.** `PatientCase` owns `ClinicalData`, `Report`, and `ChatMessage`. Deleting a case cascades.
4. **AI output fields are nullable.** `severity_score`, `risk_class`, `heatmap_path`, `confidence_score` stay NULL until the fusion model finishes and status flips to `DONE`.
5. **Temp credentials flow.** Admin-created clinicians get `must_change_password=True`. Login middleware redirects them to `/change-password` until resolved.

---

## What to do

- Read `docs/schema.md` and `docs/ui-design.md` before writing any code.
- Use Django's `AbstractUser` for the User model, named `User`.
- Use `DecimalField` or `FloatField` consistently — match what's in schema.md.
- Use Tailwind utility classes directly in templates. No custom CSS files unless absolutely necessary.
- Use Django's `{% extends 'base.html' %}` pattern. Put the sidebar + header in `base.html`.
- Use Django forms (`ModelForm` where possible) for all user input.
- Use Django's messages framework for toasts.
- Write one migration per feature phase, not per model.
- Add docstrings on models and service classes.
- Use Lucide icons via CDN or inline SVG. No icon packages.
- Use Inter font from Google Fonts.

## What NOT to do

- Do not add libraries not already in `requirements.txt` without asking.
- Do not create a REST API (DRF, etc.) — forms post directly to views.
- Do not use JWT or custom auth — Django sessions only.
- Do not create tables for `FusionModel` or `ChatBot` — they are services.
- Do not use `localStorage` or `sessionStorage`.
- Do not "improve" the color palette or typography — it's locked in `ui-design.md`.
- Do not add features not in `docs/phases.md` without asking.
- Do not generate fake/placeholder medical data in migrations — leave tables empty or use a clearly-marked `seed.py` script.
- Do not run migrations automatically — always show the commands and let the user run them.

---

## Code style

- Follow PEP 8
- Use `black` formatting (line length 100)
- Use type hints on function signatures
- Use `snake_case` for Python, `kebab-case` for URLs, `camelCase` only in JS if any
- Model fields use `snake_case` (e.g., `must_change_password`) even though UML uses `camelCase`
- One class per file when a class exceeds ~100 lines
- Imports ordered: stdlib → Django → third-party → local

---

## Running the project

```bash
# Setup
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install -r requirements.txt

# Database
python manage.py migrate
python manage.py createsuperuser  # creates first admin

# Run
python manage.py runserver
```

App runs at `http://localhost:8000`.

---

## Model placeholder

Until the real PyTorch model is trained, use `services/fusion_model.py` with a placeholder that returns random but realistic values:

```python
# Placeholder — replace when pneumonia_model.pt is ready
def diagnose(xray_path: str, clinical_data: dict) -> dict:
    return {
        "severity_score": random.uniform(0, 1),
        "risk_class": random.choice(["I", "II", "III", "IV", "V"]),
        "heatmap_path": None,  # or a sample heatmap image
        "confidence_score": random.uniform(0.6, 0.99),
    }
```

The interface must match what the real model will return, so swapping it later is a one-file change.

---

## ChatBot placeholder

Until RAG is wired up, `services/chatbot.py` returns a canned response that at least references the case context, so the UI flow works end-to-end:

```python
def process_query(query: str, case) -> str:
    return f"[Placeholder] Based on case #{case.id} (Risk Class {case.risk_class}), here is a response to: {query}"
```

---

## When stuck

- Check the relevant sequence diagram in `docs/diagrams/`
- Ask clarifying questions rather than guessing
- If a design decision isn't in the docs, flag it and wait for input
- Never invent medical logic or clinical thresholds — use the placeholder values
